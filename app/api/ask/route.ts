import { runPipeline } from '@/lib/pipeline'
import { getOpenAI, getChroma } from '@/lib/clients'

export async function POST(request: Request): Promise<Response> {
  let question: string
  try {
    const body = await request.json()
    question = typeof body?.question === 'string' ? body.question : ''
  } catch {
    return Response.json({ type: 'error', message: 'Invalid JSON body' }, { status: 400 })
  }

  if (!question) {
    return Response.json({ type: 'refusal', reason: 'empty', message: 'Please enter a question.' }, { status: 400 })
  }

  try {
    const result = await runPipeline(question, getOpenAI(), getChroma())

    // No PII in logs — log only metadata, never raw question
    console.log(JSON.stringify({
      event:       'ask',
      type:        result.type,
      reason:      result.reason,
      scheme:      result.scheme,
      chunks:      result.chunksUsed,
      model:       result.modelUsed,
      timestamp:   new Date().toISOString(),
    }))

    if (result.type === 'answer') {
      return Response.json({
        type:         'answer',
        answer:       result.text,
        source_url:   result.sourceUrl,
        last_updated: result.lastUpdated,
        scheme:       result.scheme,
      })
    }

    return Response.json({
      type:    result.type,
      reason:  result.reason,
      message: result.message,
    })

  } catch (err) {
    console.error('Pipeline error:', err instanceof Error ? err.message : err)
    return Response.json({ type: 'error', message: 'Internal server error' }, { status: 500 })
  }
}
