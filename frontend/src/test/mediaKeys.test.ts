import { describe, it, expect } from 'vitest'
import { mediaKeys } from '../api/hooks'

describe('mediaKeys', () => {
  it('all returns ["media"]', () => expect(mediaKeys.all).toEqual(['media']))
  it('browse returns ["browse", mediaType]', () =>
    expect(mediaKeys.browse('movies')).toEqual(['browse', 'movies']))
  it('browse with empty string', () =>
    expect(mediaKeys.browse('')).toEqual(['browse', '']))
  it('item returns ["item", mediaType, title]', () =>
    expect(mediaKeys.item('movies', 'Inception')).toEqual(['item', 'movies', 'Inception']))
})
