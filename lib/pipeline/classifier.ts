import type OpenAI from 'openai'

export type Intent = 'FACTUAL' | 'ADVISORY' | 'OUT_OF_SCOPE'

const ADVISORY_PHRASES = [
  'should i', 'is it good', 'is it worth', 'recommend', 'better fund',
  'which fund', 'which is better', 'should i invest', 'stop sip',
  'stop my sip', 'pause sip', 'exit now', 'exit the fund', 'compare',
  'returns comparison', 'future returns', 'will it grow', 'will it give',
  'best fund', 'better than', 'good investment', 'safe to invest',
  'right time', 'good time', 'market crash', 'should i redeem',
  'worth buying', 'is it advisable', 'advisable to',
]

const OUT_OF_SCOPE_PHRASES = [
  'stock', 'share market', 'equity market', 'nse', 'bse', 'sensex',
  'crypto', 'bitcoin', 'ethereum', 'nft',
  'fixed deposit', ' fd ', 'fd rate', 'recurring deposit',
  'insurance', 'lic', 'term plan', 'health insurance',
  'ppf', 'epf', 'nps', 'pension', 'emi', 'home loan', 'personal loan',
  'credit card', 'savings account', 'bank interest',
  'my portfolio', 'my account', 'my investment',
]

const FACTUAL_SIGNALS = [
  'expense ratio', 'exit load', 'ter ', 'sip', 'lumpsum', 'lock-in',
  'lock in', 'benchmark', 'riskometer', 'category', 'minimum investment',
  'capital gains', 'account statement', 'nav', 'aum', 'fund manager',
  'dividend', 'growth option', 'idcw', 'direct plan', 'regular plan',
  'amfi', 'sebi', 'mirae', 'kim ', 'scheme information',
]

const CLASSIFIER_PROMPT =
  'Classify this mutual fund question. Reply with exactly one word: FACTUAL, ADVISORY, or OUT_OF_SCOPE.\n' +
  'FACTUAL = asks for a specific fund fact (expense ratio, exit load, SIP amount, lock-in, benchmark, riskometer, etc.).\n' +
  'ADVISORY = asks for investment opinion, recommendation, or comparison.\n' +
  'OUT_OF_SCOPE = not about mutual funds.'

export async function classify(query: string, openai: OpenAI): Promise<Intent> {
  const q = query.toLowerCase()

  if (ADVISORY_PHRASES.some(p => q.includes(p)))   return 'ADVISORY'
  if (OUT_OF_SCOPE_PHRASES.some(p => q.includes(p))) return 'OUT_OF_SCOPE'
  if (FACTUAL_SIGNALS.some(p => q.includes(p)))     return 'FACTUAL'

  // Ambiguous — use LLM classifier
  const resp = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    temperature: 0,
    max_tokens: 10,
    messages: [
      { role: 'system', content: CLASSIFIER_PROMPT },
      { role: 'user',   content: query },
    ],
  })
  const result = resp.choices[0].message.content?.trim().toUpperCase()
  return (result === 'FACTUAL' || result === 'ADVISORY' || result === 'OUT_OF_SCOPE')
    ? result
    : 'FACTUAL'
}
