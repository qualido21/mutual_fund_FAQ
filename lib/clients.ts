/**
 * Singleton clients for OpenAI and ChromaDB.
 * Re-used across requests to avoid cold-start overhead.
 */
import OpenAI from 'openai'
import { ChromaClient } from 'chromadb'

// ---------------------------------------------------------------------------
// OpenAI
// ---------------------------------------------------------------------------

let _openai: OpenAI | null = null

export function getOpenAI(): OpenAI {
  if (!_openai) {
    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) throw new Error('OPENAI_API_KEY is not set')
    _openai = new OpenAI({ apiKey })
  }
  return _openai
}

// ---------------------------------------------------------------------------
// ChromaDB
// ---------------------------------------------------------------------------

let _chroma: ChromaClient | null = null

export function getChroma(): ChromaClient {
  if (!_chroma) {
    const url = process.env.CHROMA_URL ?? 'http://localhost:8000'
    const parsed = new URL(url)
    _chroma = new ChromaClient({
      host: parsed.hostname,
      port: parseInt(parsed.port || '8000', 10),
      ssl: parsed.protocol === 'https:',
    })
  }
  return _chroma
}
