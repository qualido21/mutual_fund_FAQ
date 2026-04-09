const PAN     = /[A-Z]{5}[0-9]{4}[A-Z]/
const AADHAAR = /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/
const PHONE   = /\b\d{10}\b/
const EMAIL   = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/
const HTML    = /<[^>]+>/g

export interface SanitizeResult {
  clean: string
  blocked: boolean
  reason?: string
}

export function sanitize(query: string): SanitizeResult {
  if (typeof query !== 'string' || !query)
    return { clean: '', blocked: true, reason: 'empty' }

  if (query.length > 500)
    return { clean: '', blocked: true, reason: 'too_long' }

  if (PAN.test(query))     return { clean: '', blocked: true, reason: 'pii_pan' }
  if (AADHAAR.test(query)) return { clean: '', blocked: true, reason: 'pii_aadhaar' }
  if (PHONE.test(query))   return { clean: '', blocked: true, reason: 'pii_phone' }
  if (EMAIL.test(query))   return { clean: '', blocked: true, reason: 'pii_email' }

  const clean = query.replace(HTML, '').replace(/\s+/g, ' ').trim()
  if (!clean) return { clean: '', blocked: true, reason: 'empty' }

  return { clean, blocked: false }
}
