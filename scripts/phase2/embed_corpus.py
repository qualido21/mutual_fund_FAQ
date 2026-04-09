"""
Corpus Embedder — Phase 2
Reads data/chunks.json, generates embeddings via OpenAI text-embedding-3-small,
and upserts into a ChromaDB collection (local persistent store).

Usage:
    export OPENAI_API_KEY=sk-...
    python scripts/embed_corpus.py               # embed all chunks
    python scripts/embed_corpus.py --source-id src_010   # embed one source
    python scripts/embed_corpus.py --reset       # drop and rebuild index
    python scripts/embed_corpus.py --info        # show collection stats

Storage: vector_store/   (ChromaDB persistent directory)
Collection: mutual-fund-faq
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent

# Load .env file if present (simple key=value parser, no dependency needed)
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())
CHUNKS_FILE   = PROJECT_ROOT / "data" / "chunks.json"
VECTOR_STORE  = PROJECT_ROOT / "vector_store"

COLLECTION_NAME   = "mutual-fund-faq"
EMBED_MODEL       = "text-embedding-3-small"
EMBED_DIMENSIONS  = 1536
BATCH_SIZE        = 100
PRICE_PER_1M_TOK  = 0.02   # USD — text-embedding-3-small as of 2025

# ChromaDB metadata values must be str/int/float/bool — no lists or None
METADATA_KEYS = ["source_id", "source_url", "source_type", "scheme_name", "fetched_at"]


# ---------------------------------------------------------------------------
# ChromaDB client
# ---------------------------------------------------------------------------

def get_chroma_collection(reset: bool = False):
    import chromadb
    from chromadb.config import Settings

    VECTOR_STORE.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[INFO] Dropped existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )
    return collection


# ---------------------------------------------------------------------------
# OpenAI embeddings
# ---------------------------------------------------------------------------

def get_openai_client():
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("       export OPENAI_API_KEY=sk-...")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def embed_batch(client, texts: list[str], local: bool = False) -> list[list[float]]:
    """Embed a batch of texts; returns list of embedding vectors."""
    if local:
        # sentence-transformers local fallback (all-MiniLM-L6-v2, 384 dims)
        return client.encode(texts, show_progress_bar=False).tolist()
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
        dimensions=EMBED_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


def get_local_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        print("[INFO] Loading local model: all-MiniLM-L6-v2 (384 dims) ...")
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        print("ERROR: sentence-transformers not installed.")
        print("       pip3 install sentence-transformers")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def chunk_to_chroma_record(chunk: dict) -> tuple[str, dict, str]:
    """Return (id, metadata, document_text) for a chunk."""
    meta = {k: (chunk.get(k) or "") for k in METADATA_KEYS}
    # Serialize list fields as comma-separated strings (ChromaDB limitation)
    meta["fact_types"] = ", ".join(chunk.get("fact_types", []))
    meta["token_count"] = chunk.get("token_count", 0)
    # Store the text in metadata for retrieval (no need for separate document store)
    meta["text"] = chunk["text"][:2000]  # ChromaDB metadata cap ~65KB; trim for safety
    return chunk["chunk_id"], meta, chunk["text"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Embed corpus chunks into ChromaDB")
    parser.add_argument("--source-id", help="Embed only chunks from this source ID")
    parser.add_argument("--reset", action="store_true", help="Drop and rebuild the entire index")
    parser.add_argument("--info", action="store_true", help="Print collection stats and exit")
    parser.add_argument("--local", action="store_true",
                        help="Use local all-MiniLM-L6-v2 model instead of OpenAI (free, 384 dims)")
    args = parser.parse_args()

    use_local = args.local

    collection = get_chroma_collection(reset=args.reset)

    if args.info:
        count = collection.count()
        print(f"Collection:  {COLLECTION_NAME}")
        print(f"Vector store: {VECTOR_STORE}")
        print(f"Total vectors: {count:,}")
        if count > 0:
            sample = collection.peek(limit=3)
            print(f"\nSample chunk IDs: {sample['ids']}")
        return

    if not CHUNKS_FILE.exists():
        print("chunks.json not found — run chunk_corpus.py first")
        sys.exit(1)

    all_chunks: list[dict] = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))

    if args.source_id:
        chunks = [c for c in all_chunks if c["source_id"] == args.source_id]
        if not chunks:
            print(f"No chunks found for source '{args.source_id}'")
            sys.exit(1)
        print(f"Embedding {len(chunks)} chunks from {args.source_id}...")
    else:
        chunks = all_chunks
        print(f"Embedding {len(chunks):,} total chunks...")

    # Find already-embedded chunk IDs to skip
    existing_ids: set[str] = set()
    if not args.reset:
        try:
            existing = collection.get(ids=[c["chunk_id"] for c in chunks])
            existing_ids = set(existing["ids"])
        except Exception:
            pass

    to_embed = [c for c in chunks if c["chunk_id"] not in existing_ids]
    skipped  = len(chunks) - len(to_embed)

    if skipped:
        print(f"  Skipping {skipped:,} already-embedded chunks")
    if not to_embed:
        print("  Nothing to embed — all chunks already in index.")
        print(f"\nCollection total: {collection.count():,} vectors")
        return

    if use_local:
        embedder = get_local_embedder()
        mode_label = "local (all-MiniLM-L6-v2, 384 dims)"
    else:
        embedder = get_openai_client()
        mode_label = f"OpenAI {EMBED_MODEL} ({EMBED_DIMENSIONS} dims)"

    print(f"  Mode: {mode_label}")
    print(f"  Embedding {len(to_embed):,} new chunks in batches of {BATCH_SIZE}...\n")

    total_tokens  = 0
    total_vectors = 0

    for batch_start in range(0, len(to_embed), BATCH_SIZE):
        batch = to_embed[batch_start: batch_start + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        ids, metadatas, documents = [], [], []
        for c in batch:
            cid, meta, doc = chunk_to_chroma_record(c)
            ids.append(cid)
            metadatas.append(meta)
            documents.append(doc)

        try:
            vectors = embed_batch(embedder, texts, local=use_local)
        except Exception as e:
            print(f"  [ERROR] Embedding batch {batch_start}–{batch_start+len(batch)}: {e}")
            time.sleep(5)
            continue

        collection.upsert(ids=ids, embeddings=vectors, metadatas=metadatas, documents=documents)

        batch_tokens = sum(c.get("token_count", 0) for c in batch)
        total_tokens  += batch_tokens
        total_vectors += len(batch)

        pct = (batch_start + len(batch)) / len(to_embed) * 100
        est_cost = total_tokens / 1_000_000 * PRICE_PER_1M_TOK
        print(
            f"  [{pct:5.1f}%] batch {batch_start // BATCH_SIZE + 1}: "
            f"{len(batch)} chunks  {batch_tokens:,} tokens  "
            f"running cost: ${est_cost:.5f}"
        )

        # Polite rate-limit pause between batches
        if batch_start + BATCH_SIZE < len(to_embed):
            time.sleep(0.5)

    total_cost = total_tokens / 1_000_000 * PRICE_PER_1M_TOK
    print(f"\n=== Embedding Summary ===")
    print(f"  Vectors added:  {total_vectors:,}")
    print(f"  Tokens used:    {total_tokens:,}")
    print(f"  API cost:       ${total_cost:.5f}")
    print(f"  Collection size: {collection.count():,} total vectors")
    print(f"  Vector store:   {VECTOR_STORE}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
