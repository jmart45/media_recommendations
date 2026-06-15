import type {
  BrowseResponse,
  ItemDetailResponse,
  MediaListResponse,
  MessageResponse,
} from './types'

/** Error thrown for any non-2xx API response, carrying the HTTP status and
 *  the FastAPI `detail` message. */
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      // non-JSON error body; fall back to statusText
    }
    throw new ApiError(res.status, detail)
  }
  return (await res.json()) as T
}

const JSON_HEADERS = { 'Content-Type': 'application/json' }

export const api = {
  listMedia: () => request<MediaListResponse>('/api/media'),

  browse: (mediaType: string) =>
    request<BrowseResponse>(`/api/browse?media_type=${encodeURIComponent(mediaType)}`),

  getItem: (mediaType: string, title: string) =>
    request<ItemDetailResponse>(
      `/api/item?media_type=${encodeURIComponent(mediaType)}&title=${encodeURIComponent(title)}`,
    ),

  updateRating: (mediaType: string, title: string, rating: number | null) =>
    request<MessageResponse>('/api/item/rating', {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify({ media_type: mediaType, title, rating }),
    }),

  updateGenre: (mediaType: string, title: string, genre: string | null) =>
    request<MessageResponse>('/api/item/genre', {
      method: 'PATCH',
      headers: JSON_HEADERS,
      body: JSON.stringify({ media_type: mediaType, title, genre }),
    }),

  deleteItem: (mediaType: string, title: string) =>
    request<MessageResponse>(
      `/api/item?media_type=${encodeURIComponent(mediaType)}&title=${encodeURIComponent(title)}`,
      { method: 'DELETE' },
    ),
}
