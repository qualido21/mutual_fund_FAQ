/**
 * Full RAG pipeline: Sanitize → Classify → Rewrite → Retrieve → Assemble → Generate
 */
import type OpenAI from 'openai'
import type { SupabaseClient } from '@supabase/supabase-js'
import { sanitize }  from './sanitizer'
import { classify }  from './classifier'
import { rewrite }   from './rewriter'
import { retrieve }  from './retriever'
import { assemble }  from './assembler'
import { generate }  from './generator'

export type { GeneratorResult } from './generator'

const REFUSAL_MESSAGES: Record<string, string> = {
  advisory:     'I can only share factual information about mutual funds. For investment advice, please consult a SEBI-registered financial advisor.',
  out_of_scope: 'This question is outside the scope of mutual funds. I can answer questions about mutual fund concepts, KYC, NAV, SIP, expense ratios, exit loads, ELSS, and specific Mirae Asset scheme facts.',
  no_context:   'I don\'t have verified information on this from official sources.',
  pii_pan:      'Please do not share personal information like your PAN card number.',
  pii_phone:    'Please do not share personal information like your phone number.',
  pii_email:    'Please do not share personal information like your email address.',
  pii_aadhaar:  'Please do not share personal information like your Aadhaar number.',
  too_long:     'Your question is too long. Please keep it under 500 characters.',
  empty:        'Please enter a question.',
}

export interface PipelineResult {
  type: 'answer' | 'refusal' | 'no_context'
  // answer fields
  text?: string
  sourceUrl?: string
  lastUpdated?: string
  scheme?: string
  modelUsed?: string
  rewrittenQuery?: string
  chunksUsed?: number
  // refusal / no_context fields
  reason?: string
  message?: string
}

export async function runPipeline(
  rawQuery: string,
  openai: OpenAI,
  supabase: SupabaseClient,
): Promise<PipelineResult> {
  // 1. Sanitize
  const sanitized = sanitize(rawQuery)
  if (sanitized.blocked) {
    const reason = sanitized.reason ?? 'empty'
    return { type: 'refusal', reason, message: REFUSAL_MESSAGES[reason] ?? REFUSAL_MESSAGES.empty }
  }

  // 2. Classify intent
  const intent = await classify(sanitized.clean, openai)
  if (intent === 'ADVISORY')
    return { type: 'refusal', reason: 'advisory', message: REFUSAL_MESSAGES.advisory }
  if (intent === 'OUT_OF_SCOPE')
    return { type: 'refusal', reason: 'out_of_scope', message: REFUSAL_MESSAGES.out_of_scope }

  // 3. Rewrite query
  const rewritten = await rewrite(sanitized.clean, openai)

  // 4. Retrieve
  const chunks = await retrieve(rewritten, openai, supabase)
  if (chunks.length === 0)
    return { type: 'no_context', message: REFUSAL_MESSAGES.no_context }

  // 5. Assemble context
  const assembled = assemble(chunks)

  // 6. Generate answer
  const genResult = await generate(
    rewritten,
    assembled.context,
    assembled.primarySourceUrl,
    assembled.primaryScheme,
    assembled.primaryFetchedAt,
    openai,
  )

  if (genResult.type !== 'answer') return genResult as PipelineResult

  return {
    ...genResult,
    rewrittenQuery: rewritten,
    chunksUsed:     assembled.chunksUsed,
  }
}
