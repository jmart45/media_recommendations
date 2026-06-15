import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { useRefreshLibrary } from '../../api/hooks'

export interface ToolCall {
  name: string
  input: unknown
}

export interface ChatEntry {
  role: 'user' | 'assistant'
  text: string
  toolCalls: ToolCall[]
}

/** SSE events emitted by the backend agent loop. */
export type ChatEvent =
  | { type: 'text'; content: string }
  | { type: 'tool_call'; name: string; input: unknown }
  | { type: 'refresh_media' }
  | { type: 'done' }

const STORAGE_KEY = 'chat_history'

export function loadHistory(): ChatEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as ChatEntry[]) : []
  } catch {
    return []
  }
}

/** Parse SSE lines from a buffer chunk. Returns parsed events and any
 *  incomplete trailing line to carry into the next chunk. */
export function parseSseLines(buffer: string): { events: ChatEvent[]; remainder: string } {
  const lines = buffer.split('\n')
  const remainder = lines.pop() ?? ''
  const events: ChatEvent[] = []
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue
    try {
      events.push(JSON.parse(line.slice(6)) as ChatEvent)
    } catch {
      // malformed line — skip
    }
  }
  return { events, remainder }
}

export function useChat() {
  const { t } = useTranslation()
  const refreshLibrary = useRefreshLibrary()
  const [messages, setMessages] = useState<ChatEntry[]>(loadHistory)
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
      // user turns which the Gemini API rejects.
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
      const updateLast = (fn: (m: ChatEntry) => ChatEntry) => {
        setMessages((prev) => {
          const next = [...prev]
          next[next.length - 1] = fn(next[next.length - 1])
          return next
        })
      }
      const applyEvent = (evt: ChatEvent) => {
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
        }
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
          if (done) {
            // Flush any remaining buffered line that arrived without a trailing \n
            if (buffer) {
              const { events } = parseSseLines(buffer + '\n')
              for (const evt of events) applyEvent(evt)
            }
            break
          }
          buffer += decoder.decode(value, { stream: true })
          const { events, remainder } = parseSseLines(buffer)
          buffer = remainder
          for (const evt of events) applyEvent(evt)
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
