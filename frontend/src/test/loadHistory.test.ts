import { describe, it, expect, beforeEach } from 'vitest'
import { loadHistory } from '../components/chat/useChat'

beforeEach(() => localStorage.clear())

describe('loadHistory', () => {
  it('returns empty array when localStorage is empty', () => {
    expect(loadHistory()).toEqual([])
  })

  it('returns parsed messages when valid JSON array is stored', () => {
    const messages = [{ role: 'user', text: 'hello', toolCalls: [] }]
    localStorage.setItem('chat_history', JSON.stringify(messages))
    expect(loadHistory()).toEqual(messages)
  })

  it('returns empty array when stored value is not an array', () => {
    localStorage.setItem('chat_history', JSON.stringify({ role: 'user' }))
    expect(loadHistory()).toEqual([])
  })

  it('returns empty array for malformed JSON', () => {
    localStorage.setItem('chat_history', '{bad json}')
    expect(loadHistory()).toEqual([])
  })

  it('returns empty array when stored value is JSON null', () => {
    localStorage.setItem('chat_history', 'null')
    expect(loadHistory()).toEqual([])
  })
})
