import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table'

import { useBrowse } from '../api/hooks'

interface Row {
  title: string
  genre: string
  rating: number | null
  year: number | null
  tmdbRating: number | null
  overview: string | null
  posterUrl: string | null
}

const columnHelper = createColumnHelper<Row>()

/** Normalize empty values to undefined so TanStack's `sortUndefined: 'last'`
 *  keeps them at the bottom in both sort directions (original behavior). */
const orUndef = <T,>(v: T | null | '' | undefined) =>
  v === null || v === '' || v === undefined ? undefined : v

export default function BrowsePage() {
  const { t } = useTranslation()
  const [params] = useSearchParams()
  const mediaType = params.get('type') ?? ''

  const { data, isLoading, isError } = useBrowse(mediaType)

  const [search, setSearch] = useState('')
  const [genre, setGenre] = useState('')
  const [ratingMode, setRatingMode] = useState<'all' | 'rated' | 'unrated'>('all')
  const [sorting, setSorting] = useState<SortingState>([{ id: 'title', desc: false }])

  const allRows: Row[] = useMemo(
    () =>
      (data?.data ?? []).map((item) => ({
        title: item.title,
        genre: item.genre ?? '',
        rating: item.rating ?? null,
        year: item.tmdb?.year ?? null,
        tmdbRating: item.tmdb?.tmdb_rating ?? null,
        overview: item.tmdb?.overview ?? null,
        posterUrl: item.tmdb?.poster_url ?? null,
      })),
    [data],
  )

  const genres = useMemo(
    () => [...new Set(allRows.map((r) => r.genre).filter(Boolean))].sort(),
    [allRows],
  )

  const filtered = useMemo(
    () =>
      allRows.filter((r) => {
        if (search && !r.title.toLowerCase().includes(search.trim().toLowerCase())) return false
        if (genre && r.genre !== genre) return false
        if (ratingMode === 'rated' && r.rating === null) return false
        if (ratingMode === 'unrated' && r.rating !== null) return false
        return true
      }),
    [allRows, search, genre, ratingMode],
  )

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: 'poster',
        header: () => null,
        cell: ({ row }) =>
          row.original.posterUrl ? (
            <img
              src={row.original.posterUrl}
              alt=""
              loading="lazy"
              className="block w-[60px] rounded-md bg-surface2"
            />
          ) : (
            <div className="flex h-[90px] w-[60px] items-center justify-center rounded-md border border-border bg-surface2 text-xl text-muted">
              ?
            </div>
          ),
      }),
      columnHelper.accessor('title', {
        header: t('col_title'),
        cell: (info) => <span className="font-semibold text-text">{info.getValue()}</span>,
      }),
      columnHelper.accessor((r) => orUndef(r.genre), {
        id: 'genre',
        header: t('col_genre'),
        sortUndefined: 'last',
        cell: ({ row }) =>
          row.original.genre ? (
            <span className="inline-block whitespace-nowrap rounded border border-border bg-surface2 px-1.5 py-0.5 text-xs text-accent2">
              {row.original.genre}
            </span>
          ) : null,
      }),
      columnHelper.accessor((r) => orUndef(r.year), {
        id: 'year',
        header: t('col_year'),
        sortUndefined: 'last',
        cell: ({ row }) => (
          <span className="whitespace-nowrap text-muted">{row.original.year ?? ''}</span>
        ),
      }),
      columnHelper.accessor((r) => orUndef(r.rating), {
        id: 'rating',
        header: t('col_my_rating'),
        sortUndefined: 'last',
        cell: ({ row }) =>
          row.original.rating !== null ? (
            <span className="whitespace-nowrap font-semibold text-star">
              ★ {row.original.rating % 1 === 0 ? `${row.original.rating}.0` : row.original.rating}
            </span>
          ) : (
            <span className="whitespace-nowrap italic text-muted">{t('unrated')}</span>
          ),
      }),
      columnHelper.accessor((r) => orUndef(r.tmdbRating), {
        id: 'tmdbRating',
        header: t('col_tmdb_rating'),
        sortUndefined: 'last',
        cell: ({ row }) => (
          <span className="whitespace-nowrap text-muted">{row.original.tmdbRating ?? ''}</span>
        ),
      }),
      columnHelper.display({
        id: 'overview',
        header: t('col_description'),
        cell: ({ row }) => (
          <span className="text-[0.82rem] leading-relaxed text-muted">
            {row.original.overview ?? ''}
          </span>
        ),
      }),
    ],
    [t],
  )

  const table = useReactTable({
    data: filtered,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <div className="mx-auto max-w-[1100px] p-6">
      <div className="mb-5 flex flex-wrap items-center gap-4">
        <h1 className="text-2xl font-bold">{isError ? '' : data?.media_type ?? mediaType}</h1>
        {!isError && data && (
          <span className="text-sm text-muted">
            {t('browse_items_count', { shown: filtered.length, total: allRows.length })}
          </span>
        )}
      </div>

      {data?.tmdb_supported && !data.tmdb_configured && (
        <div className="mb-3.5 rounded-lg border border-border bg-surface px-3.5 py-2.5 text-[0.82rem] text-muted">
          {t('tmdb_not_configured')}
        </div>
      )}

      {!isError && (
        <div className="mb-4 flex flex-wrap items-center gap-2.5">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('browse_search_placeholder')}
            className="min-w-[200px] flex-1 rounded-lg border border-border bg-surface2 px-3.5 py-2 text-sm text-text outline-none transition-colors placeholder:text-muted focus:border-accent"
          />
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className="cursor-pointer rounded-lg border border-border bg-surface2 px-2.5 py-2 text-sm text-text outline-none hover:border-accent focus:border-accent"
          >
            <option value="">{t('browse_all_genres')}</option>
            {genres.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
          <select
            value={ratingMode}
            onChange={(e) => setRatingMode(e.target.value as typeof ratingMode)}
            className="cursor-pointer rounded-lg border border-border bg-surface2 px-2.5 py-2 text-sm text-text outline-none hover:border-accent focus:border-accent"
          >
            <option value="all">{t('browse_all_ratings')}</option>
            <option value="rated">{t('browse_rated')}</option>
            <option value="unrated">{t('browse_unrated')}</option>
          </select>
        </div>
      )}

      <table className="w-full border-separate border-spacing-0 overflow-hidden rounded-xl shadow-[0_0_0_1px_var(--color-border)]">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => {
                const sortable = header.column.getCanSort()
                const sorted = header.column.getIsSorted()
                const isOverviewCol = header.id === 'overview'
                return (
                  <th
                    key={header.id}
                    onClick={sortable ? header.column.getToggleSortingHandler() : undefined}
                    className={`bg-surface2 px-3.5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted ${
                      sortable ? 'cursor-pointer select-none hover:text-text' : ''
                    } ${isOverviewCol ? 'hidden md:table-cell' : ''}`}
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {sorted === 'asc' && <span className="ml-1 text-accent2">▲</span>}
                    {sorted === 'desc' && <span className="ml-1 text-accent2">▼</span>}
                  </th>
                )
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {isLoading ? (
            <StatusRow text={t('browse_loading')} />
          ) : isError ? (
            <StatusRow text={t('browse_type_not_found')} />
          ) : filtered.length === 0 ? (
            <StatusRow text={t('browse_no_results')} />
          ) : (
            table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="transition-colors hover:bg-surface2">
                {row.getVisibleCells().map((cell) => {
                  const isOverviewCol = cell.column.id === 'overview'
                  return (
                    <td
                      key={cell.id}
                      className={`max-w-[380px] border-t border-border px-3.5 py-3 align-top text-sm ${
                        isOverviewCol ? 'hidden md:table-cell' : ''
                      }`}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  )
                })}
              </tr>
            ))
          )}
        </tbody>
      </table>

      {data?.tmdb_supported && data.tmdb_configured && (
        <p className="mt-4 text-center text-[0.72rem] text-muted">{t('tmdb_attribution')}</p>
      )}
    </div>
  )
}

function StatusRow({ text }: { text: string }) {
  return (
    <tr>
      <td colSpan={7} className="px-8 py-8 text-center italic text-muted">
        {text}
      </td>
    </tr>
  )
}
