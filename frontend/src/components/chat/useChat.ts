import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { useRefreshLibrary } from '../../api/hooks'

export interface ToolCall {
  name: string
  input: unknown
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  toolCalls: ToolCall[]
}

/** SSE events emitted by the backend agent loop. */
type ChatEvent =
  | { type: 'text'; content: string }
  | { type: 'tool_call'; name: string; input: unknown }
  | { type: 'refresh_media' }
  | { type: 'max_tokens_warning' }
  | { type: 'done' }

const STORAGE_KEY = 'chat_history'

function loadHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as ChatMessage[]) : []
  } catch {
    return []
  }
}

export function useChat() {
  const { t } = useTranslation()
  const refreshLibrary = useRefreshLibrary()
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory)
  const [streaming, setStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch {
      // storage full / unavailable — non-fatal
    }
  }, [messages])

  const sendMessage = useCallback(
    async (text: string) => {
      if (streaming) return

      // History sent to the API: all turns in order, including empty-text assistant
      // turns (tool-call-only responses). Filtering them out creates consecutive
      // user turns which the Anthropic API rejects with 422.
      const apiHistory = [
        ...messages.map((m) => ({ role: m.role, content: m.text })),
        { role: 'user', content: text },
      ]

      setMessages((prev) => [...prev, { role: 'user', text, toolCalls: [] }])
      setStreaming(true)

      const controller = new AbortController()
      abortRef.current = controller

      let assistantStarted = false
      const ensureAssistant = () => {
        if (assistantStarted) return
        assistantStarted = true
        setMessages((prev) => [...prev, { role: 'assistant', text: '', toolCalls: [] }])
      }
      const updateLast = (fn: (m: ChatMessage) => ChatMessage) => {
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = fn(next[next.length - 1])
          return next
        })
      }

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: apiHistory }),
          signal: controller.signal,
        })
        if (!res.ok || !res.body) throw new Error('chat request failed')

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            let evt: ChatEvent
            try {
              evt = JSON.parse(line.slice(6)) as ChatEvent
            } catch {
              continue
            }

            if (evt.type === 'text') {
              ensureAssistant()
              updateLast((m) => ({ ...m, text: m.text + evt.content }))
            } else if (evt.type === 'tool_call') {
              ensureAssistant()
              updateLast((m) => ({
                ...m,
                toolCalls: [...m.toolCalls, { name: evt.name, input: evt.input }],
              }))
            } else if (evt.type === 'refresh_media') {
              refreshLibrary()
            } else if (evt.type === 'max_tokens_warning') {
              setMessages((prev) => [
                ...prev,
                { role: 'assistant', text: t('max_tokens_error'), toolCalls: [] },
              ])
            }
          }
        }
      } catch {
        if (!controller.signal.aborted) {
          ensureAssistant()
          updateLast((m) => ({ ...m, text: m.text || t('error_message') }))
        }
      } finally {
        setStreaming(false)
        abortRef.current = null
      }
    },
    [messages, streaming, refreshLibrary, t],
  )

  const stop = useCallback(() => abortRef.current?.abort(), [])
  const clear = useCallback(() => setMessages([]), [])

  return { messages, streaming, sendMessage, stop, clear }
}
