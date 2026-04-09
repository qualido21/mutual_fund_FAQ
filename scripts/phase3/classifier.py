"""
Intent Classifier — Phase 3
Two-layer classifier: rule-based (free) → LLM (gpt-4o-mini, cheap).

Returns one of:
  'FACTUAL'      — specific fund fact question → proceed to retrieval
  'ADVISORY'     — investment opinion / recommendation → block
  'OUT_OF_SCOPE' — not about mutual funds → block
"""

# ---------------------------------------------------------------------------
# Layer 1 — keyword blocklists (no API call)
# ---------------------------------------------------------------------------

_ADVISORY_PHRASES = [
    "should i", "is it good", "is it worth", "recommend", "better fund",
    "which fund", "which is better", "should i invest", "stop sip",
    "stop my sip", "pause sip", "exit now", "exit the fund", "compare",
    "returns comparison", "future returns", "will it grow", "will it give",
    "best fund", "better than", "good investment", "safe to invest",
    "right time", "good time", "market crash", "should i redeem",
    "worth buying", "is it advisable", "advisable to",
]

_OUT_OF_SCOPE_PHRASES = [
    "stock", "share market", "equity market", "nse", "bse", "sensex", "nifty50",
    "crypto", "bitcoin", "ethereum", "nft",
    "fixed deposit", " fd ", "fd rate", "recurring deposit", "rd ",
    "insurance", "lic", "term plan", "health insurance",
    "ppf", "epf", "nps", "pension", "emi", "home loan", "personal loan",
    "credit card", "savings account", "bank interest",
    "my portfolio", "my account", "my investment", "my pan", "my folio",
]

# Mutual-fund factual keywords — if any present, skip LLM classifier
_FACTUAL_SIGNALS = [
    "expense ratio", "exit load", "ter ", "sip", "lumpsum", "lock-in",
    "lock in", "benchmark", "riskometer", "category", "minimum investment",
    "capital gains", "account statement", "nav", "aum", "fund manager",
    "dividend", "growth option", "idcw", "direct plan", "regular plan",
    "amfi", "sebi", "mirae", "kim ", "sid ", "scheme information",
]


def _layer1(query_lower: str):
    """Returns intent string if caught by rules, else None (pass to LLM)."""
    if any(p in query_lower for p in _ADVISORY_PHRASES):
        return "ADVISORY"
    if any(p in query_lower for p in _OUT_OF_SCOPE_PHRASES):
        return "OUT_OF_SCOPE"
    if any(p in query_lower for p in _FACTUAL_SIGNALS):
        return "FACTUAL"
    return None  # ambiguous — send to LLM


# ---------------------------------------------------------------------------
# Layer 2 — LLM classifier (gpt-4o-mini, temp=0, max_tokens=10)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "Classify this mutual fund question. Reply with exactly one word: "
    "FACTUAL, ADVISORY, or OUT_OF_SCOPE.\n"
    "FACTUAL = asks for a specific fund fact (expense ratio, exit load, SIP amount, "
    "lock-in period, benchmark, riskometer, category, minimum investment, capital gains).\n"
    "ADVISORY = asks for investment opinion, recommendation, or comparison.\n"
    "OUT_OF_SCOPE = not about mutual funds."
)


def _layer2(query: str, openai_client) -> str:
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=10,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": query},
        ],
    )
    result = resp.choices[0].message.content.strip().upper()
    return result if result in ("FACTUAL", "ADVISORY", "OUT_OF_SCOPE") else "FACTUAL"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(query: str, openai_client) -> str:
    """
    Classify query intent.
    Returns: 'FACTUAL' | 'ADVISORY' | 'OUT_OF_SCOPE'
    """
    q = query.lower()
    layer1 = _layer1(q)
    if layer1 is not None:
        return layer1
    return _layer2(query, openai_client)
