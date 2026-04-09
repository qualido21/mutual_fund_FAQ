"""
Phase 3 — Full Retrieval Pipeline
Chains: Sanitizer → Intent Classifier → Query Rewriter → Retriever → Context Assembler

Usage (CLI):
    python scripts/phase3/pipeline.py "What is the exit load for Mirae Asset Large Cap Fund?"
    python scripts/phase3/pipeline.py --verbose "What is the minimum SIP for ELSS?"

Usage (import):
    from scripts.phase3.pipeline import Pipeline
    result = Pipeline().run("What is the exit load for Mirae Asset Large Cap Fund?")
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env
_env = PROJECT_ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            k, _, v = _line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
from sanitizer  import sanitize
from classifier import classify
from rewriter   import rewrite
from retriever  import retrieve, get_supabase_client
from assembler  import assemble

# Phase 4 generator (optional — imported lazily so Phase 3 works standalone)
_PHASE4_PATH = Path(__file__).resolve().parent.parent / "phase4"
sys.path.insert(0, str(_PHASE4_PATH))
try:
    from generator import generate as _generate
    _GENERATOR_AVAILABLE = True
except ImportError:
    _GENERATOR_AVAILABLE = False

# ---------------------------------------------------------------------------
# Refusal messages
# ---------------------------------------------------------------------------

REFUSAL_MESSAGES = {
    "advisory": (
        "I can only share factual information about mutual funds. "
        "For investment advice, please consult a SEBI-registered financial advisor."
    ),
    "out_of_scope": (
        "This question is outside the scope of mutual fund facts. "
        "I can help with expense ratios, exit loads, SIP amounts, lock-in periods, "
        "riskometer ratings, benchmarks, and similar factual queries."
    ),
    "no_context": (
        "I don't have verified information on this from official sources."
    ),
    "pii_pan":     "Please do not share personal information like your PAN card number.",
    "pii_phone":   "Please do not share personal information like your phone number.",
    "pii_email":   "Please do not share personal information like your email address.",
    "pii_aadhaar": "Please do not share personal information like your Aadhaar number.",
    "too_long":    "Your question is too long. Please keep it under 500 characters.",
    "empty":       "Please enter a question.",
}

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class Pipeline:
    """
    Stateful pipeline that reuses OpenAI client and ChromaDB collection
    across multiple queries (efficient for batch / interactive use).

    Args:
        verbose:  print step-by-step logs
        generate: if True (and Phase 4 generator is available), run LLM
                  generation after retrieval and return a final answer text.
                  Default True when generator is importable.
    """

    def __init__(self, verbose: bool = False, generate: bool = True):
        self.verbose = verbose
        self._do_generate = generate and _GENERATOR_AVAILABLE
        self._openai   = None
        self._supabase = None

    # --- lazy init ---

    def _get_openai(self):
        if self._openai is None:
            from openai import OpenAI
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                print("ERROR: OPENAI_API_KEY not set in .env")
                sys.exit(1)
            self._openai = OpenAI(api_key=key)
        return self._openai

    def _get_supabase(self):
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    # --- pipeline steps ---

    def _log(self, step: str, detail: str):
        if self.verbose:
            print(f"  [{step}] {detail}", flush=True)

    def run(self, raw_query: str) -> dict:
        """
        Run the full pipeline on a raw user query.

        Returns a dict with:
            type: 'answer' | 'refusal' | 'no_context'
            -- if 'answer':
                context, primary_source_url, primary_scheme,
                primary_fetched_at, chunks_used,
                rewritten_query, intent
            -- if 'refusal':
                reason, message
            -- if 'no_context':
                message
        """
        # Step 1 — Sanitize
        sanitized = sanitize(raw_query)
        self._log("sanitize", f"blocked={sanitized.blocked} reason={sanitized.reason}")
        if sanitized.blocked:
            reason = sanitized.reason or "empty"
            return {
                "type":    "refusal",
                "reason":  reason,
                "message": REFUSAL_MESSAGES.get(reason, REFUSAL_MESSAGES["empty"]),
            }

        openai    = self._get_openai()
        supabase  = self._get_supabase()

        # Step 2 — Classify intent
        intent = classify(sanitized.clean, openai)
        self._log("classify", f"intent={intent}")
        if intent == "ADVISORY":
            return {
                "type":    "refusal",
                "reason":  "advisory",
                "message": REFUSAL_MESSAGES["advisory"],
            }
        if intent == "OUT_OF_SCOPE":
            return {
                "type":    "refusal",
                "reason":  "out_of_scope",
                "message": REFUSAL_MESSAGES["out_of_scope"],
            }

        # Step 3 — Rewrite query
        rewritten = rewrite(sanitized.clean, openai)
        self._log("rewrite", f'"{sanitized.clean}" → "{rewritten}"')

        # Step 4 — Retrieve
        chunks = retrieve(rewritten, openai, supabase)
        self._log("retrieve", f"{len(chunks)} chunks above similarity floor")
        if not chunks:
            return {
                "type":    "no_context",
                "message": REFUSAL_MESSAGES["no_context"],
            }

        # Step 5 — Assemble context
        assembled = assemble(chunks)
        self._log("assemble", f"{assembled['chunks_used']} chunks assembled")

        retrieval_result = {
            "type":               "answer",
            "intent":             intent,
            "rewritten_query":    rewritten,
            "context":            assembled["context"],
            "primary_source_url": assembled["primary_source_url"],
            "primary_scheme":     assembled["primary_scheme"],
            "primary_fetched_at": assembled["primary_fetched_at"],
            "chunks_used":        assembled["chunks_used"],
            "top_chunks":         chunks[:assembled["chunks_used"]],
        }

        if not self._do_generate:
            return retrieval_result

        # Step 6 — Generate answer (Phase 4)
        self._log("generate", "calling LLM (gpt-4o-mini) ...")
        gen_result = _generate(
            query=rewritten,
            context=assembled["context"],
            source_url=assembled["primary_source_url"],
            scheme=assembled["primary_scheme"],
            fetched_at=assembled["primary_fetched_at"],
            openai_client=openai,
        )
        self._log("generate", f"type={gen_result['type']}  model={gen_result.get('model_used', 'n/a')}")

        # Merge retrieval metadata into generation result
        if gen_result["type"] == "answer":
            gen_result.update({
                "intent":          intent,
                "rewritten_query": rewritten,
                "chunks_used":     assembled["chunks_used"],
            })
        return gen_result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run Phase 3 retrieval pipeline")
    parser.add_argument("query", nargs="?", help="Query string (or use --interactive)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show step-by-step logs")
    parser.add_argument("--interactive", "-i", action="store_true", help="REPL mode")
    parser.add_argument("--json", action="store_true", help="Output full JSON result")
    args = parser.parse_args()

    pipeline = Pipeline(verbose=args.verbose)

    def _run_and_print(q: str):
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        result = pipeline.run(q)
        if args.json:
            out = {k: v for k, v in result.items() if k not in ("context", "top_chunks")}
            print(json.dumps(out, indent=2))
        else:
            t = result["type"]
            if t == "answer":
                print(f"Type:    ANSWER  (model={result.get('model_used', 'retrieval-only')})")
                print(f"Scheme:  {result.get('scheme') or result.get('primary_scheme', '')}")
                print(f"Chunks:  {result.get('chunks_used', '?')}")
                if result.get("text"):
                    print(f"\n{result['text']}")
                else:
                    # retrieval-only mode — show top chunk snippet
                    print(f"Source:  {result.get('primary_source_url', '')}")
                    if result.get("top_chunks"):
                        c = result["top_chunks"][0]
                        print(f"\n  sim={c['similarity']}  {c['text'][:300]}{'...' if len(c['text']) > 300 else ''}")
            elif t == "refusal":
                print(f"Type:    REFUSAL ({result['reason']})")
                print(f"Message: {result['message']}")
            else:
                print(f"Type:    NO CONTEXT")
                print(f"Message: {result['message']}")

    if args.interactive:
        print("Phase 3 Pipeline — interactive mode (Ctrl+C to quit)")
        while True:
            try:
                q = input("\nQuestion: ").strip()
                if q:
                    _run_and_print(q)
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                break
    elif args.query:
        _run_and_print(args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
