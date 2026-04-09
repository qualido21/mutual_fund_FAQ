"""
Phase 3 Smoke Tests
Runs 5 factual + 5 advisory/blocked queries through the full pipeline.
Prints pass/fail for each test and writes results to data/phase3_test_results.json.

Usage:
    python scripts/phase3/test_pipeline.py
    python scripts/phase3/test_pipeline.py --verbose
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

sys.path.insert(0, str(Path(__file__).parent))
from pipeline import Pipeline

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TESTS = [
    # --- Factual queries — expect type='answer' ---
    {
        "query":       "What is the exit load for Mirae Asset Large Cap Fund?",
        "expect_type": "answer",
        "description": "Factual — exit load (Large Cap)",
    },
    {
        "query":       "What is the lock-in period for Mirae Asset ELSS Tax Saver Fund?",
        "expect_type": "answer",
        "description": "Factual — lock-in (ELSS)",
    },
    {
        "query":       "What is the minimum SIP amount for Mirae Asset ELSS?",
        "expect_type": "answer",
        "description": "Factual — min SIP (ELSS)",
    },
    {
        "query":       "What is the benchmark index for Mirae Asset Liquid Fund?",
        "expect_type": "answer",
        "description": "Factual — benchmark (Liquid)",
    },
    {
        "query":       "What is the riskometer rating of Mirae Asset Flexi Cap Fund?",
        "expect_type": "answer",
        "description": "Factual — riskometer (Flexi Cap)",
    },

    # --- Advisory queries — expect type='refusal', reason='advisory' ---
    {
        "query":       "Should I invest in Mirae Asset Large Cap Fund?",
        "expect_type": "refusal",
        "expect_reason": "advisory",
        "description": "Advisory — should I invest",
    },
    {
        "query":       "Which is a better fund: Large Cap or ELSS?",
        "expect_type": "refusal",
        "expect_reason": "advisory",
        "description": "Advisory — fund comparison",
    },
    {
        "query":       "Is it a good time to stop my SIP?",
        "expect_type": "refusal",
        "expect_reason": "advisory",
        "description": "Advisory — stop SIP recommendation",
    },

    # --- PII — expect type='refusal', reason starts with 'pii_' ---
    {
        "query":       "My PAN is ABCDE1234F, what is my exit load?",
        "expect_type": "refusal",
        "expect_reason": "pii_pan",
        "description": "PII — PAN number",
    },

    # --- Out of scope ---
    {
        "query":       "What is the current FD interest rate in SBI?",
        "expect_type": "refusal",
        "expect_reason": "out_of_scope",
        "description": "Out of scope — FD rate",
    },
]


def main():
    parser = argparse.ArgumentParser(description="Phase 3 smoke tests")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    pipeline = Pipeline(verbose=args.verbose)

    passed = 0
    failed = 0
    results = []

    print(f"Phase 3 Pipeline — {len(TESTS)} smoke tests\n" + "=" * 60)

    for i, test in enumerate(TESTS, 1):
        result = pipeline.run(test["query"])
        t = result["type"]

        type_ok   = t == test["expect_type"]
        reason_ok = True
        if "expect_reason" in test:
            reason_ok = result.get("reason", "") == test["expect_reason"]

        ok = type_ok and reason_ok
        status = "PASS" if ok else "FAIL"

        if ok:
            passed += 1
        else:
            failed += 1

        # Build detail line
        if t == "answer":
            detail = f"scheme={result['primary_scheme']!r}  chunks={result['chunks_used']}"
        elif t == "refusal":
            detail = f"reason={result['reason']!r}"
        else:
            detail = "no matching context"

        print(f"[{status}] #{i:02d} {test['description']}")
        print(f"        type={t!r}  {detail}")
        if not type_ok:
            print(f"        ↳ FAIL: expected type={test['expect_type']!r}, got {t!r}")
        if not reason_ok:
            print(f"        ↳ FAIL: expected reason={test['expect_reason']!r}, got {result.get('reason')!r}")
        print()

        results.append({
            "test":       test["description"],
            "query":      test["query"],
            "status":     status,
            "type":       t,
            "reason":     result.get("reason"),
            "scheme":     result.get("primary_scheme"),
            "chunks":     result.get("chunks_used"),
        })

    print("=" * 60)
    print(f"Results: {passed}/{len(TESTS)} passed  ({failed} failed)")

    out = PROJECT_ROOT / "data" / "phase3_test_results.json"
    out.write_text(json.dumps({"passed": passed, "failed": failed, "tests": results}, indent=2))
    print(f"Detailed results → {out}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
