"""
Vector Retriever — Phase 3
Embeds the query with text-embedding-3-small and retrieves top-K chunks
from Supabase pgvector via the match_chunks RPC function.

Threshold: similarity > 0.60
  Rationale: Natural-language questions vs. structured PDF/KIM chunks have an
  inherent semantic gap. 0.60 is the validated floor for this corpus.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

EMBED_MODEL        = "text-embedding-3-small"
EMBED_DIMENSIONS   = 1536
TOP_K              = 5          # retrieve top-5, assembler uses top-3
SIMILARITY_FLOOR   = 0.60       # enforced in SQL via match_chunks function
APPROVED_SOURCES   = ["amfi", "amc", "sebi"]


def get_supabase_client():
    """Return a Supabase client using env vars."""
    try:
        from supabase import create_client
    except ImportError:
        print("ERROR: supabase package not installed. Run: pip install supabase")
        sys.exit(1)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        print("ERROR: SUPABASE_URL not set")
        sys.exit(1)
    if not key:
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set")
        sys.exit(1)
    return create_client(url, key)


def retrieve(query: str, openai_client, supabase_client, top_k: int = TOP_K) -> list:
    """
    Embed the query and retrieve top-K chunks via Supabase match_chunks RPC.

    Returns a list of chunk dicts sorted by similarity descending.
    Only chunks above SIMILARITY_FLOOR are returned (enforced in SQL).
    Each dict has keys: text, similarity, source_url, scheme_name,
                        fact_types, source_type, fetched_at.
    """
    # Embed the query
    embedding = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=[query],
        dimensions=EMBED_DIMENSIONS,
    ).data[0].embedding

    # Call match_chunks RPC — threshold + source_type filter applied in SQL
    response = supabase_client.rpc("match_chunks", {
        "query_embedding":  embedding,
        "match_count":      top_k,
        "match_threshold":  SIMILARITY_FLOOR,
    }).execute()

    rows = response.data or []

    chunks = []
    for row in rows:
        chunks.append({
            "text":        row.get("text", ""),
            "similarity":  round(float(row.get("similarity", 0)), 4),
            "source_url":  row.get("source_url", ""),
            "scheme_name": row.get("scheme_name", ""),
            "fact_types":  row.get("fact_types", ""),
            "source_type": row.get("source_type", ""),
            "fetched_at":  row.get("fetched_at", ""),
        })

    return chunks  # already sorted by similarity desc (ORDER BY in SQL)
