import { describe, it, expect } from 'vitest'
import { kindFor } from '../components/StarRating'

describe('kindFor', () => {
  it('star 0 is empty when shown=0', () => expect(kindFor(0, 0)).toBe('empty'))
  it('star 0 is half when shown=0.5', () => expect(kindFor(0.5, 0)).toBe('half'))
  it('star 0 is full when shown=0.75', () => expect(kindFor(0.75, 0)).toBe('full'))
  it('star 0 is full when shown=1', () => expect(kindFor(1, 0)).toBe('full'))
  it('star 1 is empty when shown=1', () => expect(kindFor(1, 1)).toBe('empty'))
  it('star 1 is half when shown=1.5', () => expect(kindFor(1.5, 1)).toBe('half'))
  it('star 2 is half when shown=2.5', () => expect(kindFor(2.5, 2)).toBe('half'))
  it('star 4 is full when shown=5', () => expect(kindFor(5, 4)).toBe('full'))
  it('star 4 is empty when shown=4', () => expect(kindFor(4, 4)).toBe('empty'))
  it('star 4 is half when shown=4.5', () => expect(kindFor(4.5, 4)).toBe('half'))

  // Boundary: exactly at the full threshold (full - 0.25)
  it('star 0 is full at exactly 0.75 (full - 0.25)', () => expect(kindFor(0.75, 0)).toBe('full'))
  // Just below full threshold
  it('star 0 is half at 0.74', () => expect(kindFor(0.74, 0)).toBe('half'))
  // Exactly at half threshold (full - 0.75)
  it('star 0 is half at exactly 0.25 (full - 0.75)', () => expect(kindFor(0.25, 0)).toBe('half'))
  // Just below half threshold
  it('star 0 is empty at 0.24', () => expect(kindFor(0.24, 0)).toBe('empty'))
})
