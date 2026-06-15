import { Link, NavLink, useLocation, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useMedia } from '../api/hooks'
import LanguageSelect from './LanguageSelect'

const LINK_BASE =
  'rounded-lg px-3 py-1.5 text-sm font-semibold whitespace-nowrap transition-colors'
const LINK_ACTIVE = 'text-accent2 bg-surface2'
const LINK_IDLE = 'text-muted hover:text-text hover:bg-surface2'

export default function TopNav() {
  const { t } = useTranslation()
  const { data } = useMedia()
  const location = useLocation()
  const [params] = useSearchParams()

  const activeType =
    location.pathname === '/browse' ? params.get('type')?.toLowerCase() : null

  // One browse link per media type that actually has items.
  const types = data
    ? Object.keys(data.data)
        .filter((name) => data.data[name].length > 0)
        .sort()
    : []

  return (
    <nav className="flex h-[46px] flex-shrink-0 items-center gap-1 overflow-x-auto border-b border-border bg-surface px-4">
      <Link to="/" className="mr-2.5 text-lg no-underline" aria-label="Home">
        🍿
      </Link>

      <NavLink
        to="/"
        end
        className={({ isActive }) => `${LINK_BASE} ${isActive ? LINK_ACTIVE : LINK_IDLE}`}
      >
        {t('nav_chat')}
      </NavLink>

      {types.map((name) => {
        const isActive = activeType === name.toLowerCase()
        return (
          <Link
            key={name}
            to={`/browse?type=${encodeURIComponent(name)}`}
            className={`${LINK_BASE} ${isActive ? LINK_ACTIVE : LINK_IDLE}`}
          >
            {name}
          </Link>
        )
      })}

      <div className="ml-auto pl-2">
        <LanguageSelect />
      </div>
    </nav>
  )
}
