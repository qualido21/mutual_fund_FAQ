/**
 * Singleton clients for OpenAI and Supabase.
 * Re-used across requests to avoid cold-start overhead.
 */
import OpenAI from 'openai'
import { createClient } from '@supabase/supabase-js'
import type { SupabaseClient } from '@supabase/supabase-js'

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
// Supabase
// ---------------------------------------------------------------------------

let _supabase: SupabaseClient | null = null

export function getSupabase(): SupabaseClient {
  if (!_supabase) {
    const url = process.env.SUPABASE_URL
    const key = process.env.SUPABASE_SERVICE_ROLE_KEY
    if (!url) throw new Error('SUPABASE_URL is not set')
    if (!key) throw new Error('SUPABASE_SERVICE_ROLE_KEY is not set')
    _supabase = createClient(url, key)
  }
  return _supabase
}
