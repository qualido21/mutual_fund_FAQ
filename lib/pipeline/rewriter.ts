import type OpenAI from 'openai'

const SYSTEM_PROMPT =
  'You are a query normalizer for a mutual fund FAQ assistant. ' +
  'Rewrite the user\'s question into a clear, concise factual query in under 20 words. ' +
  'Preserve the user\'s intent exactly. If a scheme name is mentioned, keep it verbatim. ' +
  'Output only the rewritten question, nothing else.'

export async function rewrite(query: string, openai: OpenAI): Promise<string> {
  try {
    const resp = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      temperature: 0,
      max_tokens: 60,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user',   content: query },
      ],
    })
    const result = resp.choices[0].message.content?.trim()
    if (result && result.length < 300) return result
  } catch {
    // fall through
  }
  return query
}
