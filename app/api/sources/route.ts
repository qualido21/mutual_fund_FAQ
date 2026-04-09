import { readFileSync } from 'fs'
import { join } from 'path'

export async function GET(): Promise<Response> {
  try {
    const sourcesPath = join(process.cwd(), 'data', 'sources.json')
    const raw = readFileSync(sourcesPath, 'utf-8')
    const sources: Array<{
      id: string
      url: string
      type: string
      scheme?: string
      description?: string
      fetched_at?: string
    }> = JSON.parse(raw)

    return Response.json({
      total:        sources.length,
      last_updated: sources.find(s => s.fetched_at)?.fetched_at ?? null,
      sources:      sources.map(s => ({
        id:          s.id,
        url:         s.url,
        type:        s.type,
        scheme:      s.scheme ?? null,
        description: s.description ?? null,
        fetched_at:  s.fetched_at ?? null,
      })),
    })
  } catch (err) {
    console.error('Sources error:', err instanceof Error ? err.message : err)
    return Response.json({ type: 'error', message: 'Could not load sources' }, { status: 500 })
  }
}
