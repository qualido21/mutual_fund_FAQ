export interface Chunk {
  text: string
  similarity: number
  sourceUrl: string
  schemeName: string
  factTypes: string
  sourceType: string
  fetchedAt: string
}

export interface AssembledContext {
  context: string
  primarySourceUrl: string
  primaryScheme: string
  primaryFetchedAt: string
  chunksUsed: number
}

const TOP_N = 3

export function assemble(chunks: Chunk[], topN = TOP_N): AssembledContext {
  if (chunks.length === 0) {
    return { context: '', primarySourceUrl: '', primaryScheme: '', primaryFetchedAt: '', chunksUsed: 0 }
  }

  const top = chunks.slice(0, topN)
  const parts = top.map((chunk, i) =>
    `[${i + 1}] Scheme: ${chunk.schemeName || 'General'}\n` +
    `    Source: ${chunk.sourceUrl || '(not available)'}\n` +
    `    ${chunk.text}`
  )

  return {
    context:            parts.join('\n\n'),
    primarySourceUrl:   top[0].sourceUrl,
    primaryScheme:      top[0].schemeName,
    primaryFetchedAt:   top[0].fetchedAt,
    chunksUsed:         top.length,
  }
}
