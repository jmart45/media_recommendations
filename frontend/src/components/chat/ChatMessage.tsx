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
      </div>
    </div>
  )
}
