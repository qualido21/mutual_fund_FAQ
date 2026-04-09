"""
Index Validator — Phase 2
Runs 10 smoke-test queries against the ChromaDB index.
Each query has an expected scheme + fact_type; the test passes when
the top result's cosine distance is below the threshold.

Default threshold: distance < 0.40 → similarity > 0.60
Rationale: natural-language questions vs. structured PDF/KIM chunks have an
inherent semantic gap. Scores of 0.60–0.75 are meaningful; 0.75+ is
unrealistic for asymmetric Q&A-to-document retrieval.

Usage:
    export OPENAI_API_KEY=sk-...
    python scripts/validate_index.py
    python scripts/validate_index.py --threshold 0.35   # stricter
    python scripts/validate_index.py --top-k 3          # show top-3 per query
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env if present
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# ---------------------------------------------------------------------------
# Smoke-test suite
# 2 tests per scheme × 4 schemes + 2 general = 10 total
# ---------------------------------------------------------------------------

SMOKE_TESTS = [
    # --- Mirae Asset Large Cap Fund ---
    {
        "query":           "What is the expense ratio of Mirae Asset Large Cap Fund?",
        "expect_scheme":   "Mirae Asset Large Cap Fund",
        "expect_fact_type": "expense_ratio",
        "description":     "Large Cap — expense ratio",
    },
    {
        "query":           "What is the exit load for Mirae Asset Large Cap Fund?",
        "expect_scheme":   "Mirae Asset Large Cap Fund",
        "expect_fact_type": "exit_load",
        "description":     "Large Cap — exit load",
    },
    # --- Mirae Asset ELSS Tax Saver Fund ---
    {
        "query":           "What is the lock-in period for Mirae Asset ELSS Tax Saver Fund?",
        "expect_scheme":   "Mirae Asset ELSS Tax Saver Fund",
        "expect_fact_type": "lock_in",
        "description":     "ELSS — lock-in period",
    },
    {
        "query":           "What is the minimum SIP amount for Mirae Asset ELSS Tax Saver Fund?",
        "expect_scheme":   "Mirae Asset ELSS Tax Saver Fund",
        "expect_fact_type": "min_sip",
        "description":     "ELSS — minimum SIP",
    },
    # --- Mirae Asset Liquid Fund ---
    {
        "query":           "What is the exit load structure for Mirae Asset Liquid Fund?",
        "expect_scheme":   "Mirae Asset Liquid Fund",
        "expect_fact_type": "exit_load",
        "description":     "Liquid Fund — exit load (graded)",
    },
    {
        "query":           "What is the benchmark index for Mirae Asset Liquid Fund?",
        "expect_scheme":   "Mirae Asset Liquid Fund",
        "expect_fact_type": "benchmark",
        "description":     "Liquid Fund — benchmark",
    },
    # --- Mirae Asset Flexi Cap Fund ---
    {
        "query":           "What is the riskometer rating of Mirae Asset Flexi Cap Fund?",
        "expect_scheme":   "Mirae Asset Flexi Cap Fund",
        "expect_fact_type": "riskometer",
        "description":     "Flexi Cap — riskometer",
    },
    {
        "query":           "What is the minimum lumpsum investment for Mirae Asset Flexi Cap Fund?",
        "expect_scheme":   "Mirae Asset Flexi Cap Fund",
        "expect_fact_type": "min_lumpsum",
        "description":     "Flexi Cap — minimum lumpsum",
    },
    # --- General queries ---
    {
        "query":           "How do I download my capital gains statement or account statement?",
        "expect_scheme":   None,   # any scheme
        "expect_fact_type": "statement_download",
        "description":     "General — capital gains statement download",
    },
    {
        "query":           "What is the benchmark index of Mirae Asset Large Cap Fund?",
        "expect_scheme":   "Mirae Asset Large Cap Fund",
        "expect_fact_type": "benchmark",
        "description":     "Large Cap — benchmark index",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_openai_client():
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set.")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def embed_query(client, query: str, local: bool = False) -> list[float]:
    if local:
        return client.encode([query], show_progress_bar=False).tolist()[0]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[query],
        dimensions=1536,
    )
    return response.data[0].embedding


def get_chroma_collection():
    import chromadb
    vector_store = PROJECT_ROOT / "vector_store"
    if not vector_store.exists():
        print("ERROR: vector_store/ not found — run embed_corpus.py first")
        sys.exit(1)
    client = chromadb.PersistentClient(path=str(vector_store))
    try:
        return client.get_collection("mutual-fund-faq")
    except Exception:
        print("ERROR: Collection 'mutual-fund-faq' not found — run embed_corpus.py first")
        sys.exit(1)


def cosine_similarity_from_distance(distance: float) -> float:
    """ChromaDB with hnsw:space=cosine returns cosine distance (0=identical, 2=opposite)."""
    return 1.0 - distance


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def run_smoke_tests(threshold: float = 0.40, top_k: int = 1, verbose: bool = False, local: bool = False) -> bool:
    if local:
        from sentence_transformers import SentenceTransformer
        client = SentenceTransformer("all-MiniLM-L6-v2")
    else:
        client = get_openai_client()
    collection = get_chroma_collection()

    total_vectors = collection.count()
    print(f"Index:   mutual-fund-faq  ({total_vectors:,} vectors)")
    print(f"Threshold: similarity > {1 - threshold:.2f}  (distance < {threshold})")
    print(f"Tests:   {len(SMOKE_TESTS)}\n")
    print("-" * 72)

    passed = 0
    failed = 0
    results = []

    for i, test in enumerate(SMOKE_TESTS, 1):
        query_vec = embed_query(client, test["query"], local=local)

        # Query ChromaDB
        result = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["metadatas", "distances", "documents"],
        )

        top_meta     = result["metadatas"][0][0]
        top_distance = result["distances"][0][0]
        top_sim      = cosine_similarity_from_distance(top_distance)
        top_scheme   = top_meta.get("scheme_name", "")
        top_facts    = top_meta.get("fact_types", "")

        # Pass criteria
        sim_ok     = top_sim >= (1 - threshold)
        scheme_ok  = (test["expect_scheme"] is None) or (test["expect_scheme"] in top_scheme)
        fact_ok    = (test["expect_fact_type"] is None) or (test["expect_fact_type"] in top_facts)

        passed_test = sim_ok and scheme_ok
        status = "PASS" if passed_test else "FAIL"
        if passed_test:
            passed += 1
        else:
            failed += 1

        results.append({
            "test":        test["description"],
            "status":      status,
            "similarity":  round(top_sim, 4),
            "scheme":      top_scheme,
            "fact_types":  top_facts,
            "fact_match":  fact_ok,
        })

        sim_str = f"{top_sim:.4f}"
        print(f"[{status}] #{i:02d} {test['description']}")
        print(f"        similarity={sim_str}  scheme={top_scheme!r}  facts=[{top_facts}]")
        if not sim_ok:
            print(f"        ↳ FAIL: similarity {top_sim:.4f} below threshold {1-threshold:.2f}")
        if not scheme_ok:
            print(f"        ↳ FAIL: expected scheme '{test['expect_scheme']}', got '{top_scheme}'")
        if verbose and top_k > 1:
            for rank, (meta, dist) in enumerate(
                zip(result["metadatas"][0], result["distances"][0]), 1
            ):
                sim = cosine_similarity_from_distance(dist)
                print(f"        #{rank}: sim={sim:.4f}  {meta.get('scheme_name')}  [{meta.get('fact_types')}]")
        print()

    print("-" * 72)
    print(f"Results: {passed}/{len(SMOKE_TESTS)} passed  ({failed} failed)")

    # Write results to file
    out = PROJECT_ROOT / "data" / "validation_results.json"
    out.write_text(
        json.dumps({"passed": passed, "failed": failed, "tests": results}, indent=2),
        encoding="utf-8",
    )
    print(f"Detailed results → {out}")

    return failed == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Smoke-test the vector index")
    parser.add_argument("--threshold", type=float, default=0.40,
                        help="Max cosine distance to consider a match (default 0.40 → similarity > 0.60)")
    parser.add_argument("--top-k", type=int, default=1,
                        help="Number of results to retrieve per query")
    parser.add_argument("--verbose", action="store_true",
                        help="Show all top-k results per query")
    parser.add_argument("--local", action="store_true",
                        help="Use local all-MiniLM-L6-v2 embeddings (must match embed mode used)")
    args = parser.parse_args()

    all_passed = run_smoke_tests(
        threshold=args.threshold,
        top_k=args.top_k,
        verbose=args.verbose,
        local=args.local,
    )
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
