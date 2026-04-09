"""
Corpus Fetcher — Phase 1
Reads data/sources.json, fetches each URL (HTML or PDF),
parses it, and saves cleaned text + metadata to corpus/.

Usage:
    python scripts/fetch_corpus.py               # fetch all sources
    python scripts/fetch_corpus.py --id src_001  # fetch a single source
    python scripts/fetch_corpus.py --dry-run     # validate sources.json only

Output layout:
    corpus/
      raw/   src_001.html (or .pdf)
      cleaned/   src_001.txt
                 src_001.meta.json
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

# Resolve paths relative to project root (one level above scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_FILE = PROJECT_ROOT / "data" / "sources.json"
CORPUS_RAW = PROJECT_ROOT / "corpus" / "raw"
CORPUS_CLEANED = PROJECT_ROOT / "corpus" / "cleaned"

CORPUS_RAW.mkdir(parents=True, exist_ok=True)
CORPUS_CLEANED.mkdir(parents=True, exist_ok=True)

REQUEST_DELAY_SECONDS = 2  # polite crawl delay

HEADERS = {
    "User-Agent": (
        "MutualFundFAQBot/1.0 (educational research; contact: admin@example.com)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
    "Accept-Language": "en-IN,en;q=0.9",
}


# ---------------------------------------------------------------------------
# Robots.txt check
# ---------------------------------------------------------------------------

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


def _can_fetch(url: str) -> bool:
    """Return True if robots.txt permits fetching this URL."""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = base + "/robots.txt"

    if base not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            # If robots.txt is unreachable, assume allowed
            _robots_cache[base] = None
            return True
        _robots_cache[base] = rp

    rp = _robots_cache[base]
    if rp is None:
        return True
    return rp.can_fetch(HEADERS["User-Agent"], url)


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = 30) -> tuple[bytes, str]:
    """
    Fetch a URL and return (raw_bytes, content_type).
    Raises requests.HTTPError on non-2xx responses.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").lower()
    return response.content, content_type


def content_hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Save helpers
# ---------------------------------------------------------------------------

def save_raw(source_id: str, data: bytes, extension: str) -> Path:
    path = CORPUS_RAW / f"{source_id}.{extension}"
    path.write_bytes(data)
    return path


def save_cleaned(source_id: str, text: str) -> Path:
    path = CORPUS_CLEANED / f"{source_id}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def save_meta(source_id: str, meta: dict) -> Path:
    path = CORPUS_CLEANED / f"{source_id}.meta.json"
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Process a single source
# ---------------------------------------------------------------------------

def process_source(source: dict, skip_existing: bool = True) -> dict:
    """
    Fetch, parse, and save one source entry.
    Returns the updated source dict (with fetched_at and content_hash filled).
    """
    source_id = source["id"]
    url = source["url"]
    file_type = source.get("type", "html")  # "html" or "pdf"

    cleaned_path = CORPUS_CLEANED / f"{source_id}.txt"

    if skip_existing and cleaned_path.exists():
        print(f"  [SKIP] {source_id} already fetched — use --force to re-fetch")
        return source

    # Robots.txt check
    if not _can_fetch(url):
        print(f"  [BLOCKED] {source_id}: robots.txt disallows {url}")
        source["fetch_error"] = "robots_txt_blocked"
        return source

    print(f"  [FETCH] {source_id}: {url}")

    try:
        raw_bytes, content_type = fetch_url(url)
    except requests.exceptions.HTTPError as e:
        print(f"  [ERROR] {source_id}: HTTP {e.response.status_code} — {url}")
        source["fetch_error"] = f"http_{e.response.status_code}"
        return source
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] {source_id}: {e}")
        source["fetch_error"] = str(e)
        return source

    # Detect if it's really a PDF by content-type or URL
    is_pdf = "pdf" in content_type or url.lower().endswith(".pdf") or file_type == "pdf"

    # Save raw
    raw_ext = "pdf" if is_pdf else "html"
    save_raw(source_id, raw_bytes, raw_ext)

    # Parse
    if is_pdf:
        from parse_pdf import parse_pdf
        result = parse_pdf(raw_bytes, source_url=url)
        cleaned_text = result.text
        parse_meta = {
            "total_pages": result.total_pages,
            "extracted_pages": result.extracted_pages,
            "image_only_pages": result.image_only_pages,
            "has_tables": result.has_tables,
        }
    else:
        from parse_html import parse_html
        cleaned_text = parse_html(raw_bytes.decode("utf-8", errors="replace"), _source_url=url)
        parse_meta = {}

    if not cleaned_text.strip():
        print(f"  [WARN] {source_id}: parsed text is empty — check the page structure")
        source["fetch_warning"] = "empty_parsed_text"

    # Save cleaned text
    save_cleaned(source_id, cleaned_text)

    # Build and save metadata
    now = datetime.now(timezone.utc).isoformat()
    chash = content_hash(raw_bytes)

    meta = {
        "id": source_id,
        "url": url,
        "source_type": source.get("source_type"),
        "scheme_name": source.get("scheme"),
        "fact_types": source.get("fact_types", []),
        "description": source.get("description", ""),
        "fetched_at": now,
        "content_hash": chash,
        "raw_file": f"raw/{source_id}.{raw_ext}",
        "cleaned_file": f"cleaned/{source_id}.txt",
        "char_count": len(cleaned_text),
        **parse_meta,
    }
    save_meta(source_id, meta)

    # Update the source entry
    source["fetched_at"] = now
    source["content_hash"] = chash

    print(f"  [OK]    {source_id}: {len(cleaned_text):,} chars extracted")
    return source


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_sources() -> list[dict]:
    with open(SOURCES_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_sources(sources: list[dict]) -> None:
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Fetch and parse the FAQ corpus")
    parser.add_argument("--id", help="Fetch only this source ID (e.g. src_001)")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if already downloaded")
    parser.add_argument("--dry-run", action="store_true", help="Validate sources.json and exit")
    args = parser.parse_args()

    sources = load_sources()
    print(f"Loaded {len(sources)} sources from {SOURCES_FILE}\n")

    if args.dry_run:
        print("=== Dry Run: Validating sources.json ===")
        for s in sources:
            status = "✓" if s.get("url") else "✗ MISSING URL"
            print(f"  {status}  {s['id']}  {s.get('url', '')}")
        print("\nDry run complete. No files written.")
        return

    # Filter to a single source if --id provided
    if args.id:
        sources_to_fetch = [s for s in sources if s["id"] == args.id]
        if not sources_to_fetch:
            print(f"Source ID '{args.id}' not found in sources.json")
            sys.exit(1)
    else:
        sources_to_fetch = sources

    print(f"Fetching {len(sources_to_fetch)} source(s)...\n")

    updated_sources = []
    skip_existing = not args.force

    for i, source in enumerate(sources_to_fetch):
        updated = process_source(source, skip_existing=skip_existing)
        updated_sources.append(updated)

        # Add delay between requests (except after the last one)
        if i < len(sources_to_fetch) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    # Merge updated entries back into full source list
    updated_ids = {s["id"]: s for s in updated_sources}
    final_sources = [updated_ids.get(s["id"], s) for s in sources]

    save_sources(final_sources)

    # Summary
    fetched = [s for s in updated_sources if s.get("fetched_at")]
    skipped = [s for s in updated_sources if "fetch_error" not in s and not s.get("fetched_at")]
    errors = [s for s in updated_sources if "fetch_error" in s]

    print(f"\n=== Summary ===")
    print(f"  Fetched:  {len(fetched)}")
    print(f"  Skipped:  {len(skipped)} (already downloaded)")
    print(f"  Errors:   {len(errors)}")
    if errors:
        for s in errors:
            print(f"    - {s['id']}: {s.get('fetch_error')}")
    print(f"\nSources file updated: {SOURCES_FILE}")


if __name__ == "__main__":
    # Add scripts/ to path so sibling modules can be imported
    sys.path.insert(0, str(Path(__file__).parent))
    main()
