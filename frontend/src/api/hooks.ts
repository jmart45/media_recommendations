import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from './client'

export const mediaKeys = {
  all: ['media'] as const,
  browse: (mediaType: string) => ['browse', mediaType] as const,
  item: (mediaType: string, title: string) => ['item', mediaType, title] as const,
}

export function useMedia() {
  return useQuery({ queryKey: mediaKeys.all, queryFn: api.listMedia })
}

export function useBrowse(mediaType: string) {
  return useQuery({
    queryKey: mediaKeys.browse(mediaType),
    queryFn: () => api.browse(mediaType),
    enabled: mediaType.length > 0,
    retry: false,
  })
}

export function useItem(mediaType: string, title: string, enabled: boolean) {
  return useQuery({
    queryKey: mediaKeys.item(mediaType, title),
    queryFn: () => api.getItem(mediaType, title),
    enabled,
  })
}

/** Invalidate every view that reflects the library after a mutation. */
function useInvalidateLibrary() {
  const qc = useQueryClient()
  return useCallback(() => {
    qc.invalidateQueries({ queryKey: mediaKeys.all })
    qc.invalidateQueries({ queryKey: ['browse'] })
    qc.invalidateQueries({ queryKey: ['item'] })
  }, [qc])
}

export function useUpdateRating() {
  const invalidate = useInvalidateLibrary()
  return useMutation({
    mutationFn: ({ mediaType, title, rating }: { mediaType: string; title: string; rating: number | null }) =>
      api.updateRating(mediaType, title, rating),
    onSuccess: invalidate,
  })
}

export function useDeleteItem() {
  const invalidate = useInvalidateLibrary()
  return useMutation({
    mutationFn: ({ mediaType, title }: { mediaType: string; title: string }) =>
      api.deleteItem(mediaType, title),
    onSuccess: invalidate,
  })
}

/** A media refresh triggered externally (e.g. by the chat agent's SSE event). */
export function useRefreshLibrary() {
  return useInvalidateLibrary()
}
