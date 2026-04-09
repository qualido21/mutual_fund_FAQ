"""
LLM Answer Generator — Phase 4
Takes assembled context from Phase 3 and generates a ≤3-sentence,
citation-backed factual answer using OpenAI gpt-4o-mini.

Flow:
  context + query → gpt-4o-mini → output validator → ValidatedAnswer
                                       ↓ (hedging detected)
                                    gpt-4o (fallback)

Returns a dict with:
  type:        'answer' | 'refusal' | 'no_context'
  text:        the answer text (if type='answer')
  source_url:  citation URL shown to user
  last_updated: fetched_at date string
  scheme:      scheme name
  model_used:  which model generated the answer
  reason:      refusal reason (if type='refusal')
  message:     refusal message (if type='refusal')
"""

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a facts-only mutual fund information assistant for Groww.

RULES (strictly enforced):
1. Answer ONLY using the provided context. Do not use any prior knowledge.
2. Keep your answer to a maximum of 3 sentences.
3. Do NOT give investment advice, recommendations, or opinions.
4. Do NOT compare fund performance or predict returns.
5. If the context does not contain the answer, respond with exactly:
   "I don't have verified information on this."
6. Always end your answer with the Source line provided in the question.
7. Do not mention any competitor or external product.\
"""

_USER_PROMPT_TEMPLATE = """\
Context:
{context}

Question: {query}

Answer in this exact format:
[Direct factual answer in 1–3 sentences]
Source: {source_url}
Last updated: {fetched_at}\
"""

# ---------------------------------------------------------------------------
# Advisory / hedging detection
# ---------------------------------------------------------------------------

_ADVISORY_SIGNALS = [
    "recommend", "should invest", "suggest", "in my opinion",
    "i think you", "i advise", "you should",
]

_HEDGING_SIGNALS = [
    "i'm not sure", "i am not sure", "i think", "i believe",
    "it seems", "probably", "might be", "could be", "not certain",
]

# ---------------------------------------------------------------------------
# Refusal messages (mirror Phase 3 for consistency)
# ---------------------------------------------------------------------------

_REFUSAL_ADVISORY = (
    "I can only share factual information about mutual funds. "
    "For investment advice, please consult a SEBI-registered financial advisor."
)
_REFUSAL_NO_INFO = "I don't have verified information on this from official sources."

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_any(text_lower: str, signals: list) -> bool:
    return any(s in text_lower for s in signals)


def _call_llm(openai_client, model: str, user_prompt: str) -> str:
    resp = openai_client.chat.completions.create(
        model=model,
        temperature=0.1,
        max_tokens=256,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()


def _validate(raw: str, source_url: str) -> dict:
    """
    Post-generation validation.
    Returns dict with keys: ok (bool), issue (str | None).
    """
    raw_lower = raw.lower()

    # Advisory language leaked through — block
    if _has_any(raw_lower, _ADVISORY_SIGNALS):
        return {"ok": False, "issue": "advisory_leak"}

    # No-info response — pass through as no_context
    if "i don't have verified information" in raw_lower:
        return {"ok": False, "issue": "no_info"}

    # Citation missing — soft warn, not a hard block (source_url may be empty)
    if source_url and source_url not in raw:
        # Append the source line if the model forgot it
        raw += f"\nSource: {source_url}"

    return {"ok": True, "issue": None, "text": raw}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate(
    query: str,
    context: str,
    source_url: str,
    scheme: str,
    fetched_at: str,
    openai_client,
    primary_model: str = "gpt-4o-mini",
    fallback_model: str = "gpt-4o",
) -> dict:
    """
    Generate a factual answer for the query using the assembled context.

    Returns a result dict (type='answer' | 'refusal' | 'no_context').
    """
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        context=context,
        query=query,
        source_url=source_url or "(source not available)",
        fetched_at=fetched_at or "N/A",
    )

    # Primary model
    raw = _call_llm(openai_client, primary_model, user_prompt)
    model_used = primary_model

    # Fallback if hedging detected
    if _has_any(raw.lower(), _HEDGING_SIGNALS):
        raw = _call_llm(openai_client, fallback_model, user_prompt)
        model_used = fallback_model

    # Validate
    validation = _validate(raw, source_url)

    if not validation["ok"]:
        if validation["issue"] == "advisory_leak":
            return {
                "type":    "refusal",
                "reason":  "advisory",
                "message": _REFUSAL_ADVISORY,
            }
        if validation["issue"] == "no_info":
            return {
                "type":    "no_context",
                "message": _REFUSAL_NO_INFO,
            }

    return {
        "type":         "answer",
        "text":         validation.get("text", raw),
        "source_url":   source_url,
        "last_updated": fetched_at,
        "scheme":       scheme,
        "model_used":   model_used,
    }
