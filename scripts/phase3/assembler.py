"""
Context Assembler — Phase 3
Builds the LLM prompt context from the top-N retrieved chunks.

Output includes:
  - context: formatted string passed to the LLM
  - primary_source_url: highest-scoring chunk's URL (shown as citation)
  - primary_scheme: scheme name from top chunk
  - primary_fetched_at: fetch date for "last updated" display
  - chunks_used: how many chunks were included
"""

TOP_N = 3  # use top-3 chunks in context (retrieve top-5, ignore bottom-2)


def assemble(chunks: list[dict], top_n: int = TOP_N) -> dict:
    """
    Assemble context from the top-N chunks.

    Args:
        chunks: list of chunk dicts from retriever.retrieve(), sorted by similarity desc
        top_n:  max chunks to include in context

    Returns:
        dict with keys: context, primary_source_url, primary_scheme,
                        primary_fetched_at, chunks_used
    """
    if not chunks:
        return {
            "context":            "",
            "primary_source_url": "",
            "primary_scheme":     "",
            "primary_fetched_at": "",
            "chunks_used":        0,
        }

    top = chunks[:top_n]
    parts = []
    for i, chunk in enumerate(top, 1):
        scheme  = chunk["scheme_name"] or "General"
        src_url = chunk["source_url"]  or "(source URL not available)"
        text    = chunk["text"].strip()
        sim     = chunk["similarity"]
        parts.append(
            f"[{i}] Scheme: {scheme}\n"
            f"    Source: {src_url}\n"
            f"    Similarity: {sim:.4f}\n"
            f"    {text}"
        )

    primary = top[0]
    return {
        "context":            "\n\n".join(parts),
        "primary_source_url": primary["source_url"],
        "primary_scheme":     primary["scheme_name"],
        "primary_fetched_at": primary["fetched_at"],
        "chunks_used":        len(top),
    }
