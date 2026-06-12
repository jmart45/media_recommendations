import { useState, type KeyboardEvent } from 'react'

type StarKind = 'full' | 'half' | 'empty'

function StarChar({ kind }: { kind: StarKind }) {
  if (kind === 'half') {
    return (
      <span
        className="pointer-events-none block bg-clip-text text-transparent"
        style={{
          backgroundImage:
            'linear-gradient(90deg, var(--color-star) 50%, var(--color-border) 50%)',
        }}
      >
        ★
      </span>
    )
  }
  return (
    <span className={`pointer-events-none block ${kind === 'full' ? 'text-star' : 'text-border'}`}>
      ★
    </span>
  )
}

interface StarRatingProps {
  value: number | null
  onChange: (rating: number) => void
}

/** Interactive 0.5-step star rating. Mouse: hover the left/right half of each
 *  star. Keyboard: focus and use arrow keys (slider semantics). */
export default function StarRating({ value, onChange }: StarRatingProps) {
  const [hover, setHover] = useState<number | null>(null)
  const shown = hover ?? value ?? 0

  function kindFor(starIndex: number): StarKind {
    const full = starIndex + 1
    if (shown >= full - 0.25) return 'full'
    if (shown >= full - 0.75) return 'half'
    return 'empty'
  }

  function onKeyDown(e: KeyboardEvent) {
    const current = value ?? 0
    let next = current
    if (e.key === 'ArrowRight' || e.key === 'ArrowUp') next = Math.min(5, current + 0.5)
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') next = Math.max(0, current - 0.5)
    else if (e.key === 'Home') next = 0
    else if (e.key === 'End') next = 5
    else return
    e.preventDefault()
    if (next !== current) onChange(next)
  }

  return (
    <div
      role="slider"
      tabIndex={0}
      aria-label="Rating"
      aria-valuemin={0}
      aria-valuemax={5}
      aria-valuenow={value ?? 0}
      onKeyDown={onKeyDown}
      onMouseLeave={() => setHover(null)}
      className="flex items-center gap-1 rounded outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      {[0, 1, 2, 3, 4].map((i) => (
        <span
          key={i}
          className="relative h-7 w-7 text-center text-[1.7rem] leading-none"
        >
          <button
            type="button"
            tabIndex={-1}
            aria-label={`${i + 0.5} stars`}
            className="absolute inset-y-0 left-0 z-10 w-1/2 cursor-pointer"
            onMouseEnter={() => setHover(i + 0.5)}
            onClick={() => onChange(i + 0.5)}
          />
          <button
            type="button"
            tabIndex={-1}
            aria-label={`${i + 1} stars`}
            className="absolute inset-y-0 right-0 z-10 w-1/2 cursor-pointer"
            onMouseEnter={() => setHover(i + 1)}
            onClick={() => onChange(i + 1)}
          />
          <StarChar kind={kindFor(i)} />
        </span>
      ))}
    </div>
  )
}
