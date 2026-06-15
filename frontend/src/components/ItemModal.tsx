import { useEffect, useRef, useState, type ReactNode } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'

import { useDeleteItem, useItem, useUpdateGenre, useUpdateRating } from '../api/hooks'
import { formatDate } from '../lib/format'
import StarRating from './StarRating'

export interface SelectedItem {
  mediaType: string
  title: string
}

interface ItemModalProps {
  item: SelectedItem | null
  onClose: () => void
}

export default function ItemModal({ item, onClose }: ItemModalProps) {
  const { t } = useTranslation()
  const open = item !== null

  const { data, isLoading } = useItem(item?.mediaType ?? '', item?.title ?? '', open)
  const updateRating = useUpdateRating()
  const updateGenre = useUpdateGenre()
  const deleteItem = useDeleteItem()

  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [editingGenre, setEditingGenre] = useState(false)
  const [genreDraft, setGenreDraft] = useState('')
  const genreInputRef = useRef<HTMLInputElement>(null)

  // Reset state whenever the modal opens for a new item.
  useEffect(() => {
    setConfirmingDelete(false)
    setEditingGenre(false)
  }, [item])

  // Focus the genre input when editing starts.
  useEffect(() => {
    if (editingGenre) genreInputRef.current?.focus()
  }, [editingGenre])

  // Auto-cancel the delete confirmation after a few seconds.
  useEffect(() => {
    if (!confirmingDelete) return
    const id = setTimeout(() => setConfirmingDelete(false), 3000)
    return () => clearTimeout(id)
  }, [confirmingDelete])

  const detail = data?.data
  const ratingLabel =
    detail?.rating != null
      ? `${detail.rating} ${t('modal_rating_suffix')}`
      : t('modal_rating_unrated')

  function setRating(rating: number | null) {
    if (!item) return
    updateRating.mutate(
      { mediaType: item.mediaType, title: item.title, rating },
      { onSuccess: () => toast.success(t('rating_updated')) },
    )
  }

  function startEditingGenre() {
    setGenreDraft(detail?.genre ?? '')
    setEditingGenre(true)
  }

  function saveGenre() {
    if (!item) return
    const trimmed = genreDraft.trim() || null
    updateGenre.mutate(
      { mediaType: item.mediaType, title: item.title, genre: trimmed },
      {
        onSuccess: () => {
          toast.success(t('genre_updated'))
          setEditingGenre(false)
        },
      },
    )
  }

  function handleDelete() {
    if (!item) return
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    deleteItem.mutate(
      { mediaType: item.mediaType, title: item.title },
      {
        onSuccess: () => {
          toast.success(t('item_deleted', { title: item.title }))
          onClose()
        },
      },
    )
  }

  return (
    <Dialog.Root open={open} onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex w-[440px] max-w-[calc(100vw-40px)] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl">
          <div className="flex items-start justify-between gap-3 border-b border-border p-5">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-muted">
                {item?.mediaType}
              </div>
              <Dialog.Title className="text-lg font-bold leading-tight text-text">
                {detail?.title ?? item?.title}
              </Dialog.Title>
            </div>
            <Dialog.Close
              aria-label={t('modal_close_title')}
              className="rounded-md px-1.5 py-0.5 text-muted transition-colors hover:bg-surface2 hover:text-text"
            >
              ✕
            </Dialog.Close>
          </div>

          {isLoading || !detail ? (
            <div className="p-5 text-sm text-muted">{t('browse_loading')}</div>
          ) : (
            <div className="flex flex-col gap-[18px] p-5">
              <Field label={t('modal_label_genre')}>
                {editingGenre ? (
                  <div className="flex items-center gap-2">
                    <input
                      ref={genreInputRef}
                      value={genreDraft}
                      onChange={(e) => setGenreDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveGenre()
                        if (e.key === 'Escape') setEditingGenre(false)
                      }}
                      className="flex-1 rounded border border-border bg-surface2 px-2.5 py-0.5 text-sm text-text outline-none focus:border-accent"
                      placeholder={t('modal_genre_placeholder')}
                    />
                    <button
                      type="button"
                      onClick={saveGenre}
                      disabled={updateGenre.isPending}
                      className="rounded border border-border px-2.5 py-0.5 text-xs text-muted transition-colors hover:border-accent hover:text-text"
                    >
                      {t('modal_save_btn')}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingGenre(false)}
                      className="rounded border border-border px-2.5 py-0.5 text-xs text-muted transition-colors hover:border-accent hover:text-text"
                    >
                      {t('modal_cancel_btn')}
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    {detail.genre ? (
                      <span className="inline-block rounded border border-border bg-surface2 px-2.5 py-0.5 text-sm text-accent2">
                        {detail.genre}
                      </span>
                    ) : (
                      <span className="text-sm italic text-muted">{t('modal_no_genre')}</span>
                    )}
                    <button
                      type="button"
                      onClick={startEditingGenre}
                      className="rounded border border-border px-2 py-0.5 text-xs text-muted transition-colors hover:border-accent hover:text-text"
                    >
                      {t('modal_edit_btn')}
                    </button>
                  </div>
                )}
              </Field>

              <Field label={t('modal_label_rating')}>
                <div className="flex items-center gap-2">
                  <StarRating value={detail.rating ?? null} onChange={(r) => setRating(r)} />
                  <span className="min-w-[60px] text-sm text-muted">{ratingLabel}</span>
                  <button
                    type="button"
                    onClick={() => setRating(null)}
                    className="ml-1 rounded border border-border px-2 py-0.5 text-xs text-muted transition-colors hover:border-accent hover:text-text"
                  >
                    {t('modal_unrated_btn')}
                  </button>
                </div>
              </Field>

              <Field label={t('modal_label_notes')}>
                {detail.notes ? (
                  <div className="min-h-[60px] whitespace-pre-wrap rounded-lg border border-border bg-surface2 px-3 py-2.5 text-sm leading-relaxed text-text">
                    {detail.notes}
                  </div>
                ) : (
                  <span className="text-sm italic text-muted">{t('modal_no_notes')}</span>
                )}
              </Field>

              <div className="text-xs leading-relaxed text-muted">
                {t('modal_date_added')}: {formatDate(detail.created_at)}
                <br />
                {t('modal_date_updated')}: {formatDate(detail.updated_at)}
              </div>
            </div>
          )}

          <div className="flex justify-end border-t border-border p-3.5">
            <button
              type="button"
              onClick={handleDelete}
              disabled={deleteItem.isPending}
              className={`rounded-lg border px-4 py-1.5 text-sm transition-colors ${
                confirmingDelete
                  ? 'border-red-400 bg-red-400 text-white'
                  : 'border-red-400 text-red-400 hover:bg-red-400 hover:text-white'
              }`}
            >
              {confirmingDelete ? t('modal_delete_confirm') : t('modal_delete_btn')}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted">
        {label}
      </div>
      {children}
    </div>
  )
}
