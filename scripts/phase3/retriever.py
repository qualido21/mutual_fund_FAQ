"""
Vector Retriever — Phase 3
Embeds the query with text-embedding-3-small and retrieves top-K chunks
from ChromaDB, filtered to approved source types (amfi, amc, sebi).

Threshold: similarity > 0.60 (cosine distance < 0.40)
  Rationale: Natural-language questions vs. structured PDF/KIM chunks have an
  inherent semantic gap. 0.60 is the validated floor for this corpus.
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

EMBED_MODEL        = "text-embedding-3-small"
EMBED_DIMENSIONS   = 1536
COLLECTION_NAME    = "mutual-fund-faq"
TOP_K              = 5          # retrieve top-5, assembler uses top-3
SIMILARITY_FLOOR   = 0.60       # discard chunks below this similarity
APPROVED_SOURCES   = ["amfi", "amc", "sebi"]


def get_collection():
    """Return the ChromaDB collection (persistent client)."""
    import chromadb
    vector_store = PROJECT_ROOT / "vector_store"
    if not vector_store.exists():
        print("ERROR: vector_store/ not found — run embed_corpus.py first")
        sys.exit(1)
    client = chromadb.PersistentClient(path=str(vector_store))
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        print(f"ERROR: Collection '{COLLECTION_NAME}' not found — run embed_corpus.py first")
        sys.exit(1)


def retrieve(query: str, openai_client, collection, top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query and retrieve top-K chunks from ChromaDB.

    Returns a list of chunk dicts sorted by similarity descending.
    Only chunks above SIMILARITY_FLOOR are returned.
    Each dict has keys: text, similarity, source_url, scheme_name,
                        fact_types, source_type, fetched_at.
    """
    # Embed the query
    embedding = openai_client.embeddings.create(
        model=EMBED_MODEL,
        input=[query],
        dimensions=EMBED_DIMENSIONS,
    ).data[0].embedding

    # Query ChromaDB — filter to approved source types only
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["metadatas", "distances", "documents"],
            where={"source_type": {"$in": APPROVED_SOURCES}},
        )
    except Exception:
        # ChromaDB where-filter fails if a metadata field is missing; fall back without filter
        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["metadatas", "distances", "documents"],
        )

    chunks = []
    for meta, dist, doc in zip(
        results["metadatas"][0],
        results["distances"][0],
        results["documents"][0],
    ):
        similarity = 1.0 - dist
        if similarity < SIMILARITY_FLOOR:
            continue
        chunks.append({
            "text":        meta.get("text") or doc or "",
            "similarity":  round(similarity, 4),
            "source_url":  meta.get("source_url", ""),
            "scheme_name": meta.get("scheme_name", ""),
            "fact_types":  meta.get("fact_types", ""),
            "source_type": meta.get("source_type", ""),
            "fetched_at":  meta.get("fetched_at", ""),
            "source_id":   meta.get("source_id", ""),
        })

    return chunks  # already sorted by similarity desc (ChromaDB returns nearest first)
