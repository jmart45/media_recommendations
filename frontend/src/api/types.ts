import type { components } from './schema'

export type MediaItem = components['schemas']['MediaItem']
export type EnrichedMediaItem = components['schemas']['EnrichedMediaItem']
export type ItemDetail = components['schemas']['ItemDetail']
export type TmdbMeta = components['schemas']['TmdbMeta']
export type MediaTypeInfo = components['schemas']['MediaTypeInfo']

export type MediaListResponse = components['schemas']['MediaListResponse']
export type BrowseResponse = components['schemas']['BrowseResponse']
export type ItemDetailResponse = components['schemas']['ItemDetailResponse']
export type MessageResponse = components['schemas']['MessageResponse']

/** Media grouped by type name -> its items, as returned by GET /api/media. */
export type MediaByType = MediaListResponse['data']
