import { useState } from 'react'
import { useTranslation } from 'react-i18next'

import { useMedia } from '../api/hooks'
import { formatRating, getTypeIcon } from '../lib/format'
import type { MediaItem } from '../api/types'
import ItemModal, { type SelectedItem } from './ItemModal'

export default function Sidebar() {
  const { t } = useTranslation()
  const icons = t('type_icons', { returnObjects: true }) as unknown as Record<string, string>
  const { data, isLoading, isError, refetch, isFetching } = useMedia()

  const [openSections, setOpenSections] = useState<Set<string>>(new Set())
  const [selected, setSelected] = useState<SelectedItem | null>(null)

  const byType = data?.data ?? {}
  const typeNames = Object.keys(byType).sort()

  function toggle(name: string) {
    setOpenSections((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  return (
    <aside className="flex w-[300px] min-w-[220px] flex-col overflow-hidden border-r border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-4 pb-3.5 pt-[18px]">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-muted">
          {t('sidebar_heading')}
        </h2>
        <button
          type="button"
          title={t('refresh_title')}
          aria-label={t('refresh_title')}
          onClick={() => void refetch()}
          className={`rounded-md p-1 text-muted transition-colors hover:bg-surface2 hover:text-accent2 ${
            isFetching ? 'animate-spin' : ''
          }`}
        >
          ↻
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <p className="px-4 py-6 text-center text-sm text-muted">{t('browse_loading')}</p>
        ) : isError ? (
          <p className="px-4 py-6 text-center text-sm text-muted">{t('error_message')}</p>
        ) : typeNames.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm leading-relaxed text-muted">
            {t('no_types')}
            <br />
            {t('no_types_hint')}
          </div>
        ) : (
          typeNames.map((name) => (
            <TypeSection
              key={name}
              name={name}
              icon={getTypeIcon(icons, name)}
              items={byType[name]}
              isOpen={openSections.has(name)}
              onToggle={() => toggle(name)}
              onSelect={(title) => setSelected({ mediaType: name, title })}
              emptyLabel={t('no_items')}
              unratedLabel={t('unrated')}
            />
          ))
        )}
      </div>

      <ItemModal item={selected} onClose={() => setSelected(null)} />
    </aside>
  )
}

interface TypeSectionProps {
  name: string
  icon: string
  items: MediaItem[]
  isOpen: boolean
  onToggle: () => void
  onSelect: (title: string) => void
  emptyLabel: string
  unratedLabel: string
}

function TypeSection({
  name,
  icon,
  items,
  isOpen,
  onToggle,
  onSelect,
  emptyLabel,
  unratedLabel,
}: TypeSectionProps) {
  const sorted = [...items].sort((a, b) => a.title.localeCompare(b.title))

  return (
    <div className="mb-1">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        className="mx-2 flex w-[calc(100%-16px)] items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold transition-colors hover:bg-surface2"
      >
        <span className="text-lg">{icon}</span>
        <span>{name}</span>
        <span className="ml-1 text-xs text-muted">{items.length}</span>
        <span
          className={`ml-auto text-[0.6rem] text-muted transition-transform ${
            isOpen ? 'rotate-90' : ''
          }`}
        >
          ▶
        </span>
      </button>

      {isOpen && (
        <div className="px-2 pb-1 pl-4 pt-0.5">
          {sorted.length === 0 ? (
            <div className="px-2 py-1.5 text-sm italic text-muted">{emptyLabel}</div>
          ) : (
            sorted.map((item) => {
              const rating = formatRating(item.rating)
              return (
                <button
                  key={item.title}
                  type="button"
                  onClick={() => onSelect(item.title)}
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-left text-sm text-muted transition-colors hover:bg-surface2 hover:text-text"
                >
                  <span className="flex-1 truncate" title={item.title}>
                    {item.title}
                  </span>
                  {item.genre && (
                    <span className="rounded border border-border bg-surface2 px-1.5 py-px text-[0.7rem] text-accent2">
                      {item.genre}
                    </span>
                  )}
                  {rating ? (
                    <span className="whitespace-nowrap text-xs font-semibold text-star">
                      {rating}
                    </span>
                  ) : (
                    <span className="whitespace-nowrap text-xs italic text-muted">
                      {unratedLabel}
                    </span>
                  )}
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
