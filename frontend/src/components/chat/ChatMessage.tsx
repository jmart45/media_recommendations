import { useTranslation } from 'react-i18next'

import type { ChatEntry } from './useChat'
import Markdown from './Markdown'

export default function ChatMessage({ message }: { message: ChatEntry }) {
  const { t } = useTranslation()
  const isUser = message.role === 'user'

  return (
    <div
      className={`flex w-full max-w-[840px] gap-3 ${
        isUser ? 'flex-row-reverse self-end' : 'self-start'
      }`}
    >
      <div
        className={`flex h-[34px] w-[34px] flex-shrink-0 items-center justify-center rounded-full border text-base ${
          isUser ? 'border-accent bg-user' : 'border-border bg-surface2'
        }`}
      >
        {isUser ? t('avatar_user') : t('avatar_assistant')}
      </div>

      <div
        className={`max-w-[calc(100%-50px)] rounded-xl border px-4 py-3 text-sm leading-relaxed ${
          isUser ? 'border-accent bg-user' : 'border-border bg-assistant'
        }`}
      >
        {message.text && <Markdown>{message.text}</Markdown>}
        {message.toolCalls.map((tc, i) => (
          <div
            key={i}
            className="my-1 flex max-w-[600px] items-center gap-2 rounded-lg border border-border bg-tool px-3 py-1.5 font-mono text-xs text-muted"
          >
            <span className="text-accent">⚙</span>
            <span className="font-semibold text-accent2">{tc.name}</span>
            <span className="truncate">{JSON.stringify(tc.input)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
