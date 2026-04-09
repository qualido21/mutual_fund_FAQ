import { getChroma } from '@/lib/clients'

export async function GET(): Promise<Response> {
  const status: Record<string, string> = {}

  // OpenAI — just check the key is present
  status.openai = process.env.OPENAI_API_KEY ? 'configured' : 'missing_key'

  // ChromaDB — try a heartbeat
  try {
    const chroma = getChroma()
    await chroma.heartbeat()
    const collections = await chroma.listCollections()
    const hasFaq = collections.some(
      (c: { name: string }) => c.name === 'mutual-fund-faq'
    )
    status.chroma = hasFaq ? 'ok' : 'collection_missing'
  } catch {
    status.chroma = 'unreachable'
  }

  const healthy = status.openai === 'configured' && status.chroma === 'ok'

  return Response.json(
    { status: healthy ? 'ok' : 'degraded', services: status, timestamp: new Date().toISOString() },
    { status: healthy ? 200 : 503 },
  )
}
