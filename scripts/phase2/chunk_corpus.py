"""
Corpus Chunker — Phase 2
Splits cleaned corpus text files into overlapping token-bounded chunks
with full source metadata attached to every chunk.

Chunking rules (from architecture.md):
- Chunk size: 400 tokens, overlap: 50 tokens
- Respect paragraph and section boundaries
- TABLE blocks: kept whole if <400 tokens; split by row otherwise
- Every chunk carries: chunk_id, source_id, source_url, scheme_name, fact_types, fetched_at

Usage:
    python scripts/chunk_corpus.py               # chunk all sources
    python scripts/chunk_corpus.py --source-id src_010
    python scripts/chunk_corpus.py --stats       # print stats only

Output: data/chunks.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
import tiktoken

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS_CLEANED = PROJECT_ROOT / "corpus" / "cleaned"
SOURCES_FILE   = PROJECT_ROOT / "data" / "sources.json"
CHUNKS_FILE    = PROJECT_ROOT / "data" / "chunks.json"

CHUNK_TOKENS   = 400
OVERLAP_TOKENS = 50
MIN_CHUNK_CHARS = 50   # discard chunks shorter than this (chars)
MIN_CHUNK_TOKENS = 20  # discard chunks shorter than this (tokens — noise guard)

# Tokenizer — cl100k_base matches text-embedding-3-small
_enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def encode(text: str) -> list[int]:
    return _enc.encode(text)


def decode(tokens: list[int]) -> str:
    return _enc.decode(tokens)


# ---------------------------------------------------------------------------
# Segment splitter
# Splits a document into top-level segments: paragraph blocks and TABLE blocks.
# ---------------------------------------------------------------------------

_TABLE_RE = re.compile(r"\[TABLE\].*?\[/TABLE\]", re.DOTALL)
_PAGE_RE  = re.compile(r"^--- Page \d+ ---$", re.MULTILINE)


def split_into_segments(text: str) -> list[str]:
    """
    Split document text into ordered segments:
    - TABLE blocks are kept as atomic segments
    - Everything else is split by double newlines (paragraphs)
    - Page markers (--- Page N ---) are dropped (not content)
    """
    # Remove page markers
    text = _PAGE_RE.sub("", text)

    segments: list[str] = []
    last = 0
    for m in _TABLE_RE.finditer(text):
        # Text before this table
        pre = text[last:m.start()].strip()
        if pre:
            # Split prose into paragraphs
            for para in re.split(r"\n{2,}", pre):
                para = para.strip()
                if para:
                    segments.append(para)
        # The table itself
        table_text = m.group(0).strip()
        if table_text:
            segments.append(table_text)
        last = m.end()

    # Remaining text after last table
    tail = text[last:].strip()
    if tail:
        for para in re.split(r"\n{2,}", tail):
            para = para.strip()
            if para:
                segments.append(para)

    return [s for s in segments if len(s) >= MIN_CHUNK_CHARS]


# ---------------------------------------------------------------------------
# Table row splitter (for large tables)
# ---------------------------------------------------------------------------

def split_table_by_rows(table_text: str) -> list[str]:
    """
    Split a TABLE block into per-row chunks, keeping the header row
    in every chunk for context.
    """
    inner = re.sub(r"^\[TABLE\]\n?", "", table_text)
    inner = re.sub(r"\n?\[/TABLE\]$", "", inner)

    rows = [r.strip() for r in inner.splitlines() if r.strip()]
    if not rows:
        return []

    header = rows[0]
    separator = rows[1] if (len(rows) > 1 and re.match(r"^[-| ]+$", rows[1])) else None
    data_start = 2 if separator else 1

    data_rows = rows[data_start:]
    if not data_rows:
        return [f"[TABLE]\n{inner}\n[/TABLE]"]

    chunks = []
    for row in data_rows:
        piece = f"[TABLE]\n{header}"
        if separator:
            piece += f"\n{separator}"
        piece += f"\n{row}\n[/TABLE]"
        if len(piece) >= MIN_CHUNK_CHARS:
            chunks.append(piece)
    return chunks


# ---------------------------------------------------------------------------
# Core chunker
# ---------------------------------------------------------------------------

def chunk_segment(segment: str) -> list[str]:
    """
    Split a single segment into ≤CHUNK_TOKENS token chunks with OVERLAP_TOKENS overlap.
    Tables < CHUNK_TOKENS are returned as-is; larger tables are split by row.
    """
    # Table handling
    if segment.startswith("[TABLE]"):
        if count_tokens(segment) <= CHUNK_TOKENS:
            return [segment]
        else:
            return split_table_by_rows(segment)

    tokens = encode(segment)
    if len(tokens) <= CHUNK_TOKENS:
        return [segment]

    # Sliding window over token ids
    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_TOKENS, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = decode(chunk_tokens).strip()
        if len(chunk_text) >= MIN_CHUNK_CHARS:
            chunks.append(chunk_text)
        if end >= len(tokens):
            break
        # Step forward by (CHUNK_TOKENS - OVERLAP_TOKENS) to create overlap
        start += CHUNK_TOKENS - OVERLAP_TOKENS

    return chunks


def chunk_document(text: str, source_meta: dict) -> list[dict]:
    """
    Chunk a full document and return a list of chunk dicts with metadata.
    """
    segments = split_into_segments(text)
    chunks: list[dict] = []

    source_id   = source_meta["id"]
    source_url  = source_meta["url"]
    scheme_name = source_meta.get("scheme")
    fact_types  = source_meta.get("fact_types", [])
    fetched_at  = source_meta.get("fetched_at", "")

    chunk_index = 0
    for segment in segments:
        for sub_chunk in chunk_segment(segment):
            sub_chunk = sub_chunk.strip()
            if len(sub_chunk) < MIN_CHUNK_CHARS:
                continue
            token_count = count_tokens(sub_chunk)
            if token_count < MIN_CHUNK_TOKENS:
                continue
            chunk_id = f"{source_id}_chunk_{chunk_index:04d}"
            chunks.append({
                "chunk_id":    chunk_id,
                "text":        sub_chunk,
                "source_id":   source_id,
                "source_url":  source_url,
                "source_type": source_meta.get("source_type", ""),
                "scheme_name": scheme_name or "General",
                "fact_types":  fact_types,
                "token_count": token_count,
                "fetched_at":  fetched_at,
            })
            chunk_index += 1

    return chunks


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_sources() -> list[dict]:
    return json.loads(SOURCES_FILE.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Chunk cleaned corpus into embedding-ready pieces")
    parser.add_argument("--source-id", help="Chunk only this source")
    parser.add_argument("--stats", action="store_true", help="Print stats from existing chunks.json and exit")
    args = parser.parse_args()

    if args.stats:
        if not CHUNKS_FILE.exists():
            print("chunks.json not found — run without --stats first")
            sys.exit(1)
        chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
        by_source: dict[str, list] = {}
        for c in chunks:
            by_source.setdefault(c["source_id"], []).append(c)
        print(f"Total chunks: {len(chunks)}")
        print(f"Sources:      {len(by_source)}")
        total_tokens = sum(c["token_count"] for c in chunks)
        print(f"Total tokens: {total_tokens:,}")
        print()
        for sid, cs in sorted(by_source.items()):
            avg_tok = sum(c["token_count"] for c in cs) // len(cs)
            print(f"  {sid}: {len(cs):>4} chunks  avg {avg_tok} tok/chunk")
        return

    sources = load_sources()
    if args.source_id:
        sources = [s for s in sources if s["id"] == args.source_id]
        if not sources:
            print(f"Source '{args.source_id}' not found")
            sys.exit(1)

    all_chunks: list[dict] = []
    skipped = 0

    print(f"Chunking {len(sources)} source(s)...\n")
    for source in sources:
        sid = source["id"]
        txt_path = CORPUS_CLEANED / f"{sid}.txt"

        if not txt_path.exists() or txt_path.stat().st_size < MIN_CHUNK_CHARS:
            print(f"  [SKIP] {sid}: empty or missing cleaned text")
            skipped += 1
            continue

        text = txt_path.read_text(encoding="utf-8")
        chunks = chunk_document(text, source)

        if not chunks:
            print(f"  [WARN] {sid}: produced 0 chunks")
            skipped += 1
            continue

        total_tokens = sum(c["token_count"] for c in chunks)
        avg_tokens   = total_tokens // len(chunks)
        print(f"  [OK]  {sid}: {len(chunks):>4} chunks  {total_tokens:>7,} tokens  avg {avg_tokens} tok/chunk")
        all_chunks.extend(chunks)

    # Merge with existing chunks if chunking a subset
    if args.source_id and CHUNKS_FILE.exists():
        existing = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
        existing = [c for c in existing if c["source_id"] != args.source_id]
        all_chunks = existing + all_chunks

    CHUNKS_FILE.write_text(
        json.dumps(all_chunks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n=== Chunking Summary ===")
    print(f"  Total chunks:  {len(all_chunks):,}")
    print(f"  Skipped:       {skipped}")
    total_tok = sum(c["token_count"] for c in all_chunks)
    print(f"  Total tokens:  {total_tok:,}")
    est_cost = total_tok / 1_000_000 * 0.02   # $0.02 / 1M tokens for text-embedding-3-small
    print(f"  Est. embed cost (text-embedding-3-small): ${est_cost:.4f}")
    print(f"\nOutput: {CHUNKS_FILE}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
