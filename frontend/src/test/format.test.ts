import { describe, it, expect } from 'vitest'
import { formatRating, formatDate, getTypeIcon } from '../lib/format'

describe('formatRating', () => {
  it('returns null for null', () => expect(formatRating(null)).toBeNull())
  it('returns null for undefined', () => expect(formatRating(undefined)).toBeNull())
  it('formats whole number with .0 suffix', () => expect(formatRating(4)).toBe('★ 4.0'))
  it('formats 0 as 0.0', () => expect(formatRating(0)).toBe('★ 0.0'))
  it('formats 5 as 5.0', () => expect(formatRating(5)).toBe('★ 5.0'))
  it('formats half-step rating', () => expect(formatRating(4.5)).toBe('★ 4.5'))
  it('formats 0.5', () => expect(formatRating(0.5)).toBe('★ 0.5'))
})

describe('formatDate', () => {
  it('returns em dash for null', () => expect(formatDate(null)).toBe('—'))
  it('returns em dash for undefined', () => expect(formatDate(undefined)).toBe('—'))
  it('returns em dash for empty string', () => expect(formatDate('')).toBe('—'))
  it('returns non-empty string for valid ISO date', () => {
    const result = formatDate('2024-06-15T00:00:00Z')
    expect(result).toBeTruthy()
    expect(result).toContain('2024')
  })
})

describe('getTypeIcon', () => {
  const icons = { movies: '🎬', tv: '📺', _default: '📦' }

  it('returns icon for known key (lowercase match)', () =>
    expect(getTypeIcon(icons, 'movies')).toBe('🎬'))
  it('is case-insensitive', () =>
    expect(getTypeIcon(icons, 'Movies')).toBe('🎬'))
  it('falls back to _default for unknown key', () =>
    expect(getTypeIcon(icons, 'games')).toBe('📦'))
  it('falls back to first two uppercase chars when no _default', () =>
    expect(getTypeIcon({ movies: '🎬' }, 'books')).toBe('BO'))
  it('handles single-char name gracefully', () =>
    expect(getTypeIcon({}, 'X')).toBe('X'))
  it('handles empty name', () =>
    expect(getTypeIcon({}, '')).toBe(''))
})
