"""
Fact Extractor — Phase 1
Reads cleaned corpus text files and extracts structured scheme facts
using regex patterns. Outputs data/scheme_facts.json.

Extracted facts per scheme:
  - scheme_name, category, expense_ratio, exit_load
  - min_sip, min_lumpsum, lock_in, benchmark, riskometer
  - source_url, fetched_at

Usage:
    python scripts/extract_facts.py
    python scripts/extract_facts.py --source-id src_006   # single file
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_CLEANED = PROJECT_ROOT / "corpus" / "cleaned"
SOURCES_FILE = PROJECT_ROOT / "data" / "sources.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "scheme_facts.json"


# ---------------------------------------------------------------------------
# Regex patterns for each fact type
# ---------------------------------------------------------------------------

PATTERNS = {
    "expense_ratio": [
        # KIM/SID format: "The AMC has estimated that upto 2.25% of the daily net assets"
        r"(?:upto|up to)\s+([0-9]+\.[0-9]+\s*%)\s+of\s+the\s+daily\s+net\s+assets",
        # "maximum recurring expenses...2.25%"
        r"maximum\s+recurring\s+expenses[^.]{0,200}?([0-9]+\.[0-9]+\s*%)",
        # Standard label format: "expense ratio: 0.54%"
        r"(?:expense ratio|total expense ratio|TER)[:\s]+([0-9]+\.[0-9]+\s*%[^.\n]{0,60})",
        # "0.54% per annum" near "expense"
        r"([0-9]+\.[0-9]+\s*%\s*(?:per annum|p\.a\.))[^.\n]{0,40}expense",
    ],
    "exit_load": [
        # KIM bullet format: "• If redeemed within 1 year (365 days) from the date of allotment: 1%"
        r"If redeemed within\s+1\s+year[^:]{0,40}:\s*([0-9.]+%[^\n]{0,60})",
        # Graded exit load (Liquid funds): "Day 1: 0.0070%, Day 2: 0.0065%..."
        r"Day\s+1[^:]*:\s*([0-9.]+%[^\n]{0,100})",
        # Standard label: "exit load: 1%..."
        r"exit\s*load[:\s]+([0-9.]+%[^\n]{0,80})",
    ],
    "min_sip": [
        # KIM format: "Investments through SIP: Rs. 99/- and in multiples of Re.1/-"
        r"(?:Investments?\s+through\s+SIP|SIP)[:\s]+Rs\.\s*([0-9,]+)/?-",
        # "minimum SIP: ₹500"
        r"(?:minimum\s+SIP(?:\s+amount)?|SIP\s+minimum)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)",
        # "Rs. 99/- and in multiples...SIP"
        r"Rs\.\s*([0-9,]+)/-\s+and\s+in\s+multiples[^.\n]{0,60}SIP",
    ],
    "min_lumpsum": [
        # KIM format: "minimum investment of Rs.5,000/- and in multiples"
        r"minimum\s+investment\s+of\s+Rs\.\s*([0-9,]+)/?-\s+and\s+in\s+multiples",
        r"(?:minimum\s+(?:lump\s*sum|lumpsum|one.time|purchase)(?:\s+amount)?)[:\s]+(?:Rs\.?|₹|INR)?\s*([0-9,]+)",
        r"(?:Rs\.?|₹|INR)\s*([0-9,]+)[^.\n]{0,40}(?:lump\s*sum|one.time purchase)",
    ],
    "lock_in": [
        # "lock-in period: 3 years" or "lock in: nil"
        r"lock.in\s*(?:period)?[:\s]+([^\n]{3,80})",
        r"([0-9]+\s+(?:year|month)s?\s+lock.in)",
    ],
    "benchmark": [
        # "Benchmark: Nifty 100 TRI"
        r"(?:benchmark|scheme benchmark)[:\s]+([^\n]{5,100})",
        r"(?:compared|benchmarked)\s+(?:with|against)\s+([^\n]{5,80})",
    ],
    "riskometer": [
        # KIM/SID: "investors who are seeking* Very High *risk"
        r"investors?\s+who\s+are\s+seeking\*?\s+((?:Very\s+High|High|Moderately\s+High|Moderate|Moderately\s+Low|Low))\s*\*?\s*risk",
        # "principal will be at Very High risk" (website format)
        r"principal[^.]{0,60}(Very\s+High|High|Moderately\s+High|Moderate|Moderately\s+Low|Low)\s+risk",
        # Standalone riskometer label
        r"(?:risk\s*level|product\s*label|riskometer)[:\s]+(Very\s+High|High|Moderately\s+High|Moderate|Moderately\s+Low|Low)",
        # Liquid/Debt funds: Potential Risk Class Matrix format "B-I", "A-II", etc.
        r"POTENTIAL\s+RISK\s+CLASS\s+MATRIX[^)]{0,300}\(Class\s+[ABC]\)\s+([A-C]-[I]{1,3})",
    ],
    "category": [
        # "Category: Large Cap Fund" or "Type: Equity"
        r"(?:category|scheme\s+category|type\s+of\s+scheme)[:\s]+([^\n]{5,80})",
        r"(?:an?\s+)(Large Cap|Mid Cap|Small Cap|Flexi Cap|ELSS|Liquid|Debt|Hybrid)\s+(?:Fund|Scheme)",
    ],
    "statement_download": [
        # How to download capital gains / account statement
        r"(?:download|get)\s+(?:your\s+)?(?:capital\s+gains?\s+statement|account\s+statement)[^.\n]{0,200}",
        r"CAMS|KFintech|Karvy[^.\n]{0,150}statement",
    ],
}

# Map fact_type to a human-friendly label used as dict key
FACT_LABELS = {
    "expense_ratio": "expense_ratio",
    "exit_load": "exit_load",
    "min_sip": "min_sip",
    "min_lumpsum": "min_lumpsum",
    "lock_in": "lock_in",
    "benchmark": "benchmark",
    "riskometer": "riskometer",
    "category": "category",
    "statement_download": "statement_download",
}

# Riskometer canonical values for normalization
RISKOMETER_VALUES = [
    "Very High", "High", "Moderately High", "Moderate", "Moderately Low", "Low"
]


def _normalize_riskometer(raw: str) -> Optional[str]:
    raw_lower = raw.lower().strip()
    for val in RISKOMETER_VALUES:
        if val.lower() in raw_lower:
            return val
    return raw.strip()


def _clean_match(text: str, fact_type: str = "") -> str:
    """Strip trailing punctuation, boilerplate prefixes, and excess whitespace."""
    text = text.strip().rstrip(".,;:()")
    text = re.sub(r"\s+", " ", text)

    if fact_type == "benchmark":
        # Remove KIM prefix "Index The benchmark of the scheme is"
        text = re.sub(r"^(?:Index\s+)?The\s+benchmark\s+of\s+the\s+scheme\s+is\s+", "", text, flags=re.IGNORECASE)
        # Remove trailing context "(Total Return index). The same..."
        text = re.sub(r"\.\s+The\s+same.*$", "", text, flags=re.IGNORECASE)
        # Remove leading "(Total"
        text = re.sub(r"^\(Total\s+", "", text)
        text = text.strip().rstrip(")")

    if fact_type == "lock_in":
        # Only keep if it contains a duration or "nil"
        if not re.search(r"\d+\s*(?:year|month)|nil|none|no lock", text, re.IGNORECASE):
            return ""
        # Extract "3 years" or "nil" from noisy text
        m = re.search(r"(\d+\s+years?|nil|none)", text, re.IGNORECASE)
        if m:
            text = m.group(1)

    return text


def extract_facts_from_text(text: str, fact_types: list[str]) -> dict:
    """
    Run regex patterns against cleaned text and return extracted facts.
    Only runs patterns for fact_types listed in the source metadata.
    """
    facts = {}

    for fact_type in fact_types:
        if fact_type not in PATTERNS:
            continue

        for pattern in PATTERNS[fact_type]:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                raw_value = match.group(1) if match.lastindex else match.group(0)
                cleaned = _clean_match(raw_value, fact_type)

                if fact_type == "riskometer":
                    cleaned = _normalize_riskometer(cleaned)

                # Only store if we got something non-empty
                if len(cleaned) >= 1:
                    facts[FACT_LABELS[fact_type]] = cleaned
                    break  # first successful pattern wins

    return facts


def build_scheme_record(source: dict, facts: dict) -> dict:
    """Build a standardized scheme fact record."""
    return {
        "scheme_name": source.get("scheme") or "General",
        "source_id": source["id"],
        "source_url": source["url"],
        "source_type": source.get("source_type"),
        "description": source.get("description", ""),
        "fetched_at": source.get("fetched_at"),
        # Extracted facts (present only if found)
        **{k: v for k, v in facts.items()},
    }


def merge_scheme_records(records: list[dict]) -> list[dict]:
    """
    Merge multiple records for the same scheme_name into one,
    preferring AMC-sourced values over AMFI over SEBI,
    and KIM/PDF values over HTML scheme pages.
    """
    SOURCE_PRIORITY = {"amc": 1, "amfi": 2, "sebi": 3}
    by_scheme: dict[str, dict] = {}

    for record in records:
        scheme = record.get("scheme_name") or "General"

        if scheme not in by_scheme:
            by_scheme[scheme] = dict(record)
            continue

        existing = by_scheme[scheme]
        priority_new = SOURCE_PRIORITY.get(record.get("source_type", ""), 9)
        priority_existing = SOURCE_PRIORITY.get(existing.get("source_type", ""), 9)

        # Merge: fill missing fields, prefer lower priority number
        fact_keys = list(FACT_LABELS.values())
        for key in fact_keys:
            if key not in existing and key in record:
                existing[key] = record[key]
            elif key in record and priority_new < priority_existing:
                existing[key] = record[key]

        # Accumulate all source URLs
        existing_urls = existing.get("all_source_urls", [existing.get("source_url")])
        if record["source_url"] not in existing_urls:
            existing_urls.append(record["source_url"])
        existing["all_source_urls"] = existing_urls

    return list(by_scheme.values())


def process_source(source: dict) -> Optional[dict]:
    """Load cleaned text for a source and extract facts."""
    source_id = source["id"]
    cleaned_path = CORPUS_CLEANED / f"{source_id}.txt"

    if not cleaned_path.exists():
        print(f"  [SKIP] {source_id}: cleaned text not found — run fetch_corpus.py first")
        return None

    text = cleaned_path.read_text(encoding="utf-8")
    fact_types = source.get("fact_types", [])

    facts = extract_facts_from_text(text, fact_types)
    record = build_scheme_record(source, facts)

    found = [k for k in FACT_LABELS.values() if k in facts]
    print(f"  [OK]  {source_id} ({source.get('scheme', 'general')}): found {found}")

    return record


def main():
    parser = argparse.ArgumentParser(description="Extract structured facts from corpus")
    parser.add_argument("--source-id", help="Process only this source ID")
    args = parser.parse_args()

    with open(SOURCES_FILE, encoding="utf-8") as f:
        sources = json.load(f)

    if args.source_id:
        sources = [s for s in sources if s["id"] == args.source_id]
        if not sources:
            print(f"Source '{args.source_id}' not found")
            sys.exit(1)

    print(f"Extracting facts from {len(sources)} source(s)...\n")

    records = []
    for source in sources:
        record = process_source(source)
        if record:
            records.append(record)

    merged = merge_scheme_records(records)

    # Merge in manual facts (riskometer, category, lock_in verified from official website)
    manual_file = PROJECT_ROOT / "data" / "manual_facts.json"
    if manual_file.exists():
        manual_entries = json.loads(manual_file.read_text(encoding="utf-8"))
        manual_by_scheme = {e["scheme_name"]: e for e in manual_entries}
        for record in merged:
            manual = manual_by_scheme.get(record["scheme_name"])
            if not manual:
                continue
            # Manual values fill gaps; they also override noisy regex extractions for
            # fields that are image-rendered in PDFs (riskometer, category, lock_in)
            override_keys = {"riskometer", "category", "lock_in"}
            for key, val in manual.items():
                if key in ("scheme_name", "note"):
                    continue
                if key in override_keys or key not in record:
                    record[key] = val
        print("\nManual facts merged for verified fields (riskometer, category, lock_in).")

    OUTPUT_FILE.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n=== Extraction Summary ===")
    print(f"  Sources processed: {len(records)}")
    print(f"  Schemes merged:    {len(merged)}")
    for scheme_record in merged:
        found_facts = [k for k in FACT_LABELS.values() if k in scheme_record]
        print(f"  {scheme_record['scheme_name']}: {found_facts}")
    print(f"\nOutput written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
