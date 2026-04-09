"""
Corpus Embedder — Phase 2
Reads data/chunks.json, generates embeddings via OpenAI text-embedding-3-small,
and upserts into Supabase pgvector (mutual_fund_chunks table).

Usage:
    python scripts/phase2/embed_corpus.py               # embed all chunks
    python scripts/phase2/embed_corpus.py --source-id src_010   # embed one source
    python scripts/phase2/embed_corpus.py --reset       # truncate table and rebuild
    python scripts/phase2/embed_corpus.py --info        # show table row count

Requires:
    pip install openai supabase
    OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY in .env
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env (simple parser — no extra dependency needed)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

CHUNKS_FILE       = PROJECT_ROOT / "data" / "chunks.json"
COLLECTION_NAME   = "mutual_fund_chunks"   # Supabase table name
EMBED_MODEL       = "text-embedding-3-small"
EMBED_DIMENSIONS  = 1536
BATCH_SIZE        = 100
PRICE_PER_1M_TOK  = 0.02   # USD — text-embedding-3-small as of 2025


# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

def get_supabase_client():
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed.")
        print("       pip install supabase")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        print("ERROR: SUPABASE_URL environment variable not set.")
        sys.exit(1)
    if not key:
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable not set.")
        sys.exit(1)
    return create_client(url, key)


# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

def get_openai_client():
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def embed_batch(client, texts: list) -> list:
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
        dimensions=EMBED_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def _clean(s: str) -> str:
    """Strip null bytes and other characters PostgreSQL text cannot store."""
    return s.replace("\x00", "") if s else s


def chunk_to_row(chunk: dict, embedding: list) -> dict:
    """Convert a chunk dict + embedding into a Supabase table row."""
    fact_types = chunk.get("fact_types", [])
    if isinstance(fact_types, list):
        fact_types = ", ".join(fact_types)
    return {
        "chunk_id":    chunk["chunk_id"],
        "text":        _clean(chunk["text"]),
        "embedding":   embedding,
        "source_id":   chunk.get("source_id", ""),
        "source_url":  chunk.get("source_url", ""),
        "source_type": chunk.get("source_type", ""),
        "scheme_name": chunk.get("scheme_name", ""),
        "fact_types":  fact_types,
        "fetched_at":  chunk.get("fetched_at", ""),
        "token_count": chunk.get("token_count", 0),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Embed corpus chunks into Supabase pgvector")
    parser.add_argument("--source-id", help="Embed only chunks from this source ID")
    parser.add_argument("--reset", action="store_true", help="Truncate the table and rebuild from scratch")
    parser.add_argument("--info", action="store_true", help="Print table row count and exit")
    args = parser.parse_args()

    supabase = get_supabase_client()
    openai   = get_openai_client()

    if args.info:
        resp = supabase.table(COLLECTION_NAME).select("chunk_id", count="exact").execute()
        print(f"Table:         {COLLECTION_NAME}")
        print(f"Total vectors: {resp.count:,}")
        return

    if args.reset:
        supabase.table(COLLECTION_NAME).delete().neq("chunk_id", "").execute()
        print(f"[INFO] Truncated table '{COLLECTION_NAME}'")

    if not CHUNKS_FILE.exists():
        print("chunks.json not found — run chunk_corpus.py first")
        sys.exit(1)

    all_chunks: list = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

    if args.source_id:
        chunks = [c for c in all_chunks if c["source_id"] == args.source_id]
        if not chunks:
            print(f"No chunks found for source '{args.source_id}'")
            sys.exit(1)
        print(f"Embedding {len(chunks)} chunks from {args.source_id}...")
    else:
        chunks = all_chunks
        print(f"Embedding {len(chunks):,} total chunks...")

    # Find already-embedded chunk IDs to skip (unless reset)
    existing_ids: set = set()
    if not args.reset:
        chunk_ids = [c["chunk_id"] for c in chunks]
        # Query in batches of 500 (Supabase IN limit)
        for i in range(0, len(chunk_ids), 500):
            batch_ids = chunk_ids[i:i + 500]
            resp = supabase.table(COLLECTION_NAME).select("chunk_id").in_("chunk_id", batch_ids).execute()
            existing_ids.update(row["chunk_id"] for row in (resp.data or []))

    to_embed = [c for c in chunks if c["chunk_id"] not in existing_ids]
    skipped  = len(chunks) - len(to_embed)

    if skipped:
        print(f"  Skipping {skipped:,} already-embedded chunks")
    if not to_embed:
        print("  Nothing to embed — all chunks already in table.")
        return

    print(f"  Model: OpenAI {EMBED_MODEL} ({EMBED_DIMENSIONS} dims)")
    print(f"  Embedding {len(to_embed):,} new chunks in batches of {BATCH_SIZE}...\n")

    total_tokens  = 0
    total_vectors = 0

    for batch_start in range(0, len(to_embed), BATCH_SIZE):
        batch = to_embed[batch_start: batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        try:
            vectors = embed_batch(openai, texts)
        except Exception as e:
            print(f"  [ERROR] Embedding batch {batch_start}–{batch_start + len(batch)}: {e}")
            time.sleep(5)
            continue

        rows = [chunk_to_row(c, v) for c, v in zip(batch, vectors)]

        try:
            supabase.table(COLLECTION_NAME).upsert(rows, on_conflict="chunk_id").execute()
        except Exception as e:
            print(f"  [ERROR] Upsert batch {batch_start}–{batch_start + len(batch)}: {e}")
            continue

        batch_tokens  = sum(c.get("token_count", 0) for c in batch)
        total_tokens  += batch_tokens
        total_vectors += len(batch)

        pct      = (batch_start + len(batch)) / len(to_embed) * 100
        est_cost = total_tokens / 1_000_000 * PRICE_PER_1M_TOK
        print(
            f"  [{pct:5.1f}%] batch {batch_start // BATCH_SIZE + 1}: "
            f"{len(batch)} chunks  {batch_tokens:,} tokens  "
            f"running cost: ${est_cost:.5f}"
        )

        if batch_start + BATCH_SIZE < len(to_embed):
            time.sleep(0.3)

    total_cost = total_tokens / 1_000_000 * PRICE_PER_1M_TOK
    print(f"\n=== Embedding Summary ===")
    print(f"  Vectors added:  {total_vectors:,}")
    print(f"  Tokens used:    {total_tokens:,}")
    print(f"  API cost:       ${total_cost:.5f}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
