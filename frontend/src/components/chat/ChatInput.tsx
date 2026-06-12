import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

interface ChatInputProps {
  onSend: (text: string) => void
  onStop: () => void
  streaming: boolean
}

export default function ChatInput({ onSend, onStop, streaming }: ChatInputProps) {
  const { t } = useTranslation()
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function resize() {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  function submit() {
    const text = value.trim()
    if (!text || streaming) return
    onSend(text)
    setValue('')
    requestAnimationFrame(resize)
  }

  return (
    <div className="flex items-end gap-3 border-t border-border bg-surface px-6 py-4">
      <textarea
        ref={textareaRef}
        rows={1}
        value={value}
        placeholder={t('input_placeholder')}
        onChange={(e) => {
          setValue(e.target.value)
          resize()
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
        className="max-h-40 flex-1 resize-none rounded-lg border border-border bg-surface2 px-4 py-3 text-sm leading-relaxed text-text outline-none transition-colors placeholder:text-muted focus:border-accent"
      />

      {streaming ? (
        <button
          type="button"
          title={t('stop_title')}
          aria-label={t('stop_title')}
          onClick={onStop}
          className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-surface2 text-text transition-transform hover:bg-border active:scale-95"
        >
          ◼
        </button>
      ) : (
        <button
          type="button"
          title={t('send_title')}
          aria-label={t('send_title')}
          onClick={submit}
          disabled={!value.trim()}
          className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-accent text-white transition-transform hover:bg-accent2 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
        >
          ➤
        </button>
      )}
    </div>
  )
}
