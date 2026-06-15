import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'

import { useChat } from './useChat'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'

interface WelcomeItem {
  label: string
  example: string
}

export default function Chat() {
  const { t } = useTranslation()
  const { messages, streaming, sendMessage, stop, clear } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, streaming])

  const welcomeItems = t('welcome_items', { returnObjects: true }) as unknown as WelcomeItem[]
  const showTyping = streaming && messages[messages.length - 1]?.role === 'user'

  return (
    <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-border bg-surface px-6 pb-3.5 pt-[18px]">
        <div>
          <h1 className="text-lg font-bold">{t('chat_heading')}</h1>
          <p className="mt-0.5 text-xs text-muted">{t('chat_subtitle')}</p>
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={clear}
            className="rounded-md border border-border px-2.5 py-1 text-xs text-muted transition-colors hover:border-accent hover:text-text"
          >
            {t('clear_chat')}
          </button>
        )}
      </header>

      <div ref={scrollRef} className="flex flex-1 flex-col gap-4 overflow-y-auto px-6 py-5">
        {messages.length === 0 && (
          <div className="flex w-full max-w-[840px] gap-3 self-start">
            <div className="flex h-[34px] w-[34px] flex-shrink-0 items-center justify-center rounded-full border border-border bg-surface2 text-base">
              {t('avatar_assistant')}
            </div>
            <div className="max-w-[calc(100%-50px)] rounded-xl border border-border bg-assistant px-4 py-3 text-sm leading-relaxed">
              <p className="mb-2">{t('welcome_intro')}</p>
              <ul className="my-1.5 list-disc pl-5">
                {welcomeItems.map((item) => (
                  <li key={item.label} className="my-0.5">
                    <strong className="text-accent2">{item.label}</strong> — e.g. "{item.example}"
                  </li>
                ))}
              </ul>
              <p className="mt-2">{t('welcome_outro')}</p>
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} />
        ))}

        {showTyping && (
          <div className="flex w-full max-w-[840px] gap-3 self-start">
            <div className="flex h-[34px] w-[34px] flex-shrink-0 items-center justify-center rounded-full border border-border bg-surface2 text-base">
              {t('avatar_assistant')}
            </div>
            <div className="flex items-center gap-1 rounded-xl border border-border bg-assistant px-4 py-4">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted"
                  style={{ animationDelay: `${i * 0.2}s` }}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <ChatInput onSend={sendMessage} onStop={stop} streaming={streaming} />
    </main>
  )
}
