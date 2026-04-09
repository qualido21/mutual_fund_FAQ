"""
Query Rewriter — Phase 3
Normalizes colloquial or incomplete queries into clear factual questions.

Examples:
  "whats the exit load"         → "What is the exit load for Mirae Asset funds?"
  "min sip amount for elss"     → "What is the minimum SIP amount for Mirae Asset ELSS Tax Saver Fund?"
  "how risky is large cap fund" → "What is the riskometer rating of Mirae Asset Large Cap Fund?"
"""

_SYSTEM_PROMPT = (
    "You are a query normalizer for a mutual fund FAQ assistant. "
    "Rewrite the user's question into a clear, concise factual query in under 20 words. "
    "Preserve the user's intent exactly — do not add opinions or assumptions. "
    "If a scheme name is mentioned, keep it verbatim. "
    "Output only the rewritten question, nothing else."
)


def rewrite(query: str, openai_client) -> str:
    """
    Rewrite query for better vector retrieval.
    Returns the rewritten query string (falls back to original on error).
    """
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=60,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": query},
            ],
        )
        rewritten = resp.choices[0].message.content.strip()
        # Sanity check: rewritten should be non-empty and not too long
        if rewritten and len(rewritten) < 300:
            return rewritten
    except Exception:
        pass
    return query  # fallback to original
