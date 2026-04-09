import type OpenAI from 'openai'
import { ChromaClient, IncludeEnum } from 'chromadb'
import type { Chunk } from './assembler'

const EMBED_MODEL      = 'text-embedding-3-small'
const EMBED_DIMENSIONS = 1536
const COLLECTION_NAME  = 'mutual-fund-faq'
const TOP_K            = 5
const SIMILARITY_FLOOR = 0.60
const APPROVED_SOURCES = ['amfi', 'amc', 'sebi']

export async function retrieve(
  query: string,
  openai: OpenAI,
  chroma: ChromaClient,
): Promise<Chunk[]> {
  // Embed the query
  const embResp = await openai.embeddings.create({
    model: EMBED_MODEL,
    input: [query],
    dimensions: EMBED_DIMENSIONS,
  })
  const queryEmbedding = embResp.data[0].embedding

  // Get collection
  const collection = await chroma.getCollection({ name: COLLECTION_NAME })

  // Query with source-type filter; fall back without filter if it fails
  let results
  try {
    results = await collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: TOP_K,
      where: { source_type: { $in: APPROVED_SOURCES } },
      include: [IncludeEnum.metadatas, IncludeEnum.distances, IncludeEnum.documents],
    })
  } catch {
    results = await collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: TOP_K,
      include: [IncludeEnum.metadatas, IncludeEnum.distances, IncludeEnum.documents],
    })
  }

  const chunks: Chunk[] = []
  const metadatas  = results.metadatas[0]  ?? []
  const distances  = results.distances[0]  ?? []
  const documents  = results.documents[0]  ?? []

  for (let i = 0; i < metadatas.length; i++) {
    const similarity = 1 - (distances[i] ?? 1)
    if (similarity < SIMILARITY_FLOOR) continue

    const meta = metadatas[i] ?? {}
    chunks.push({
      text:        (meta['text'] as string) || (documents[i] ?? ''),
      similarity:  Math.round(similarity * 10000) / 10000,
      sourceUrl:   (meta['source_url']  as string) ?? '',
      schemeName:  (meta['scheme_name'] as string) ?? '',
      factTypes:   (meta['fact_types']  as string) ?? '',
      sourceType:  (meta['source_type'] as string) ?? '',
      fetchedAt:   (meta['fetched_at']  as string) ?? '',
    })
  }

  return chunks // already sorted by similarity desc
}
