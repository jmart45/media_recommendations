import { useTranslation } from 'react-i18next'

import { SUPPORTED_LANGS } from '../i18n'

export default function LanguageSelect() {
  const { i18n } = useTranslation()
  const current = i18n.resolvedLanguage ?? 'en'

  return (
    <select
      aria-label="Language"
      value={current}
      onChange={(e) => void i18n.changeLanguage(e.target.value)}
      className="cursor-pointer rounded-md border border-border bg-surface2 px-1.5 py-1 text-xs text-muted outline-none transition-colors hover:border-accent hover:text-text focus:border-accent"
    >
      {SUPPORTED_LANGS.map((lang) => (
        <option key={lang} value={lang}>
          {lang.toUpperCase()}
        </option>
      ))}
    </select>
  )
}
