/** "★ 4.0" / "★ 4.5", or null when unrated. */
export function formatRating(rating: number | null | undefined): string | null {
  if (rating === null || rating === undefined) return null
  return `★ ${rating % 1 === 0 ? `${rating}.0` : rating}`
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/** Pick an emoji for a media type from the i18n type_icons map, falling back
 *  to a default icon, then to the first two letters of the name. */
export function getTypeIcon(icons: Record<string, string>, name: string): string {
  return icons[name.toLowerCase()] || icons._default || name.slice(0, 2).toUpperCase()
}
