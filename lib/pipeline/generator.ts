import type OpenAI from 'openai'

const SYSTEM_PROMPT = `You are a facts-only mutual fund information assistant.

RULES (strictly enforced):
1. Answer ONLY using the provided context. Do not use any prior knowledge.
2. For simple definitions: 2–4 sentences. For conceptual questions: up to 8 sentences with structure if helpful.
3. Do NOT give investment advice, recommendations, or opinions.
4. Do NOT compare fund performance or predict returns.
5. If the context does not contain the answer, respond with exactly: "I don't have verified information on this."
6. Always end your answer with the Source line provided in the question.
7. Do not mention any competitor or external product.
8. Use plain text. No markdown headers. You may use bullet points sparingly for lists.`

const USER_PROMPT = (
  context: string,
  query: string,
  sourceUrl: string,
  fetchedAt: string,
) => `Context:
${context}

Question: ${query}

Answer in this exact format:
[Direct factual answer in 1–3 sentences]
Source: ${sourceUrl || '(source not available)'}
Last updated: ${fetchedAt || 'N/A'}`

const ADVISORY_SIGNALS = ['recommend', 'should invest', 'suggest', 'in my opinion', 'you should']
const HEDGING_SIGNALS  = ["i'm not sure", 'i am not sure', 'i think', 'i believe', 'it seems', 'probably', 'might be', 'could be', 'not certain']

export interface GeneratorResult {
  type: 'answer' | 'refusal' | 'no_context'
  text?: string
  sourceUrl?: string
  lastUpdated?: string
  scheme?: string
  modelUsed?: string
  reason?: string
  message?: string
}

async function callLLM(openai: OpenAI, model: string, userPrompt: string): Promise<string> {
  const resp = await openai.chat.completions.create({
    model,
    temperature: 0.1,
    max_tokens: 512,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user',   content: userPrompt },
    ],
  })
  return resp.choices[0].message.content?.trim() ?? ''
}

export async function generate(
  query: string,
  context: string,
  sourceUrl: string,
  scheme: string,
  fetchedAt: string,
  openai: OpenAI,
  primaryModel = 'gpt-4o-mini',
  fallbackModel = 'gpt-4o',
): Promise<GeneratorResult> {
  const prompt = USER_PROMPT(context, query, sourceUrl, fetchedAt)

  let raw = await callLLM(openai, primaryModel, prompt)
  let modelUsed = primaryModel

  // Fallback if hedging detected
  if (HEDGING_SIGNALS.some(s => raw.toLowerCase().includes(s))) {
    raw = await callLLM(openai, fallbackModel, prompt)
    modelUsed = fallbackModel
  }

  const lower = raw.toLowerCase()

  if (ADVISORY_SIGNALS.some(s => lower.includes(s))) {
    return {
      type: 'refusal', reason: 'advisory',
      message: 'I can only share factual information about mutual funds. For investment advice, please consult a SEBI-registered financial advisor.',
    }
  }

  if (lower.includes("i don't have verified information")) {
    return { type: 'no_context', message: 'I don\'t have verified information on this from official sources.' }
  }

  // Append source if model omitted it
  if (sourceUrl && !raw.includes(sourceUrl)) {
    raw += `\nSource: ${sourceUrl}`
  }

  return { type: 'answer', text: raw, sourceUrl, lastUpdated: fetchedAt, scheme, modelUsed }
}
