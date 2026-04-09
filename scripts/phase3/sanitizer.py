"""
Input Sanitizer — Phase 3
Runs before any LLM call. Fast, rule-based, zero API cost.

Blocks:
  - Inputs over 500 characters
  - PII patterns: PAN, phone, email, Aadhaar
  - Empty / whitespace-only inputs
Cleans:
  - Strips HTML tags
  - Normalizes whitespace
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SanitizeResult:
    clean: str
    blocked: bool
    reason: Optional[str] = None


# PII patterns
_PAN      = re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]')
_PHONE    = re.compile(r'\b\d{10}\b')
_EMAIL    = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
_AADHAAR  = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
_HTML_TAG = re.compile(r'<[^>]+>')


def sanitize(query: str) -> SanitizeResult:
    """Sanitize a raw user query. Returns SanitizeResult with .blocked and .clean."""
    if not isinstance(query, str):
        return SanitizeResult("", True, "invalid_type")

    if len(query) > 500:
        return SanitizeResult("", True, "too_long")

    if _PAN.search(query):
        return SanitizeResult("", True, "pii_pan")

    if _AADHAAR.search(query):
        return SanitizeResult("", True, "pii_aadhaar")

    if _PHONE.search(query):
        return SanitizeResult("", True, "pii_phone")

    if _EMAIL.search(query):
        return SanitizeResult("", True, "pii_email")

    clean = _HTML_TAG.sub("", query)
    clean = " ".join(clean.split())

    if not clean:
        return SanitizeResult("", True, "empty")

    return SanitizeResult(clean, False)
