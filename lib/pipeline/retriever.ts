import type OpenAI from 'openai'
import type { SupabaseClient } from '@supabase/supabase-js'
import type { Chunk } from './assembler'

const EMBED_MODEL      = 'text-embedding-3-small'
const EMBED_DIMENSIONS = 1536
const TOP_K            = 5
const SIMILARITY_FLOOR = 0.60

interface MatchChunkRow {
  chunk_id:    string
  text:        string
  source_url:  string
  source_type: string
  scheme_name: string
  fact_types:  string
  fetched_at:  string
  similarity:  number
}

export async function retrieve(
  query: string,
  openai: OpenAI,
  supabase: SupabaseClient,
): Promise<Chunk[]> {
  // Embed the query
  const embResp = await openai.embeddings.create({
    model: EMBED_MODEL,
    input: [query],
    dimensions: EMBED_DIMENSIONS,
  })
  const queryEmbedding = embResp.data[0].embedding

  // PostgREST requires vector passed as a string e.g. "[0.1,0.2,...]"
  const { data, error } = await supabase.rpc('match_chunks', {
    query_embedding:  `[${queryEmbedding.join(',')}]`,
    match_count:      TOP_K,
    match_threshold:  SIMILARITY_FLOOR,
  })

  if (error) throw new Error(`Supabase retrieval error: ${error.message}`)
  if (!data || (data as MatchChunkRow[]).length === 0) return []

  return (data as MatchChunkRow[]).map(row => ({
    text:       row.text,
    similarity: Math.round(row.similarity * 10000) / 10000,
    sourceUrl:  row.source_url  ?? '',
    schemeName: row.scheme_name ?? '',
    factTypes:  row.fact_types  ?? '',
    sourceType: row.source_type ?? '',
    fetchedAt:  row.fetched_at  ?? '',
  }))
}
