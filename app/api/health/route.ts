import { getSupabase } from '@/lib/clients'

export async function GET(): Promise<Response> {
  const status: Record<string, string> = {}

  // OpenAI — just check the key is present
  status.openai = process.env.OPENAI_API_KEY ? 'configured' : 'missing_key'

  // Supabase — try a lightweight RPC to verify connectivity and table existence
  try {
    const supabase = getSupabase()
    const { error } = await supabase
      .from('mutual_fund_chunks')
      .select('chunk_id', { count: 'exact', head: true })
    status.supabase = error ? `error: ${error.message}` : 'ok'
  } catch (e) {
    status.supabase = `unreachable: ${e instanceof Error ? e.message : e}`
  }

  const healthy = status.openai === 'configured' && status.supabase === 'ok'

  return Response.json(
    { status: healthy ? 'ok' : 'degraded', services: status, timestamp: new Date().toISOString() },
    { status: healthy ? 200 : 503 },
  )
}
