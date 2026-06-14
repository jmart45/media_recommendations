import { describe, it, expect } from 'vitest'
import { parseSseLines } from '../components/chat/useChat'

describe('parseSseLines', () => {
  it('parses a single complete line', () => {
    const { events, remainder } = parseSseLines('data: {"type":"done"}\n')
    expect(events).toHaveLength(1)
    expect(events[0]).toEqual({ type: 'done' })
    expect(remainder).toBe('')
  })

  it('carries incomplete final line into remainder', () => {
    const { events, remainder } = parseSseLines('data: {"type":"done"}\ndata: {"type":"tex')
    expect(events).toHaveLength(1)
    expect(remainder).toBe('data: {"type":"tex')
  })

  it('parses multiple events in one chunk', () => {
    const chunk = 'data: {"type":"text","content":"hi"}\ndata: {"type":"done"}\n'
    const { events } = parseSseLines(chunk)
    expect(events).toHaveLength(2)
    expect(events[0]).toEqual({ type: 'text', content: 'hi' })
    expect(events[1]).toEqual({ type: 'done' })
  })

  it('skips lines without data: prefix', () => {
    const { events } = parseSseLines('event: message\ndata: {"type":"done"}\n')
    expect(events).toHaveLength(1)
  })

  it('skips malformed JSON lines', () => {
    const { events } = parseSseLines('data: {bad json}\ndata: {"type":"done"}\n')
    expect(events).toHaveLength(1)
    expect(events[0]).toEqual({ type: 'done' })
  })

  it('returns empty events and empty remainder for empty input', () => {
    const { events, remainder } = parseSseLines('')
    expect(events).toHaveLength(0)
    expect(remainder).toBe('')
  })

  it('parses tool_call event', () => {
    const line = 'data: {"type":"tool_call","name":"add_media_item","input":{"title":"Dune"}}\n'
    const { events } = parseSseLines(line)
    expect(events[0]).toEqual({
      type: 'tool_call',
      name: 'add_media_item',
      input: { title: 'Dune' },
    })
  })

  it('parses refresh_media event', () => {
    const { events } = parseSseLines('data: {"type":"refresh_media"}\n')
    expect(events[0]).toEqual({ type: 'refresh_media' })
  })
})
