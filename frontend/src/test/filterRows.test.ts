import { describe, it, expect } from 'vitest'
import { filterRows } from '../pages/BrowsePage'

const rows = [
  { title: 'Dune', genre: 'Sci-Fi', rating: 4.5, year: 2021, tmdbRating: 7.8, overview: null, posterUrl: null },
  { title: 'The Shining', genre: 'Horror', rating: 5.0, year: 1980, tmdbRating: 8.4, overview: null, posterUrl: null },
  { title: 'Inception', genre: 'Thriller', rating: null, year: 2010, tmdbRating: 8.8, overview: null, posterUrl: null },
  { title: 'dune part two', genre: 'Sci-Fi', rating: null, year: 2024, tmdbRating: null, overview: null, posterUrl: null },
]

describe('filterRows', () => {
  it('returns all rows when filters are empty', () => {
    expect(filterRows(rows, '', '', 'all')).toHaveLength(4)
  })

  it('filters by title substring (case-insensitive)', () => {
    const result = filterRows(rows, 'dune', '', 'all')
    expect(result.map((r) => r.title)).toEqual(['Dune', 'dune part two'])
  })

  it('trims whitespace from search term', () => {
    const result = filterRows(rows, '  dune  ', '', 'all')
    expect(result).toHaveLength(2)
  })

  it('filters by exact genre', () => {
    const result = filterRows(rows, '', 'Sci-Fi', 'all')
    expect(result.map((r) => r.title)).toEqual(['Dune', 'dune part two'])
  })

  it('ratingMode=rated excludes null ratings', () => {
    const result = filterRows(rows, '', '', 'rated')
    expect(result.every((r) => r.rating !== null)).toBe(true)
    expect(result).toHaveLength(2)
  })

  it('ratingMode=unrated excludes non-null ratings', () => {
    const result = filterRows(rows, '', '', 'unrated')
    expect(result.every((r) => r.rating === null)).toBe(true)
    expect(result).toHaveLength(2)
  })

  it('combines search + genre + ratingMode', () => {
    const result = filterRows(rows, 'dune', 'Sci-Fi', 'unrated')
    expect(result.map((r) => r.title)).toEqual(['dune part two'])
  })

  it('returns empty array when nothing matches', () => {
    expect(filterRows(rows, 'nonexistent', '', 'all')).toHaveLength(0)
  })
})
