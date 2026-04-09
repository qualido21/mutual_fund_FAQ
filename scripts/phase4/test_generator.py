"""
Phase 4 End-to-End Smoke Tests
Runs the full pipeline (Phase 3 retrieval + Phase 4 generation) on
5 factual questions and verifies that:
  - type == 'answer'
  - answer text is non-empty
  - source URL is present in the answer
  - answer contains no advisory language

Also runs 3 guard-rail checks (advisory / PII / out-of-scope) to confirm
Phase 3 blocking still works with Phase 4 wired in.

Usage:
    python scripts/phase4/test_generator.py
    python scripts/phase4/test_generator.py --verbose
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

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "phase3"))
from pipeline import Pipeline

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TESTS = [
    # --- Factual — expect a real answer with source URL ---
    {
        "query":        "What is the exit load for Mirae Asset Large Cap Fund?",
        "expect_type":  "answer",
        "check_source": True,
        "description":  "Factual — exit load (Large Cap)",
    },
    {
        "query":        "What is the lock-in period for Mirae Asset ELSS Tax Saver Fund?",
        "expect_type":  "answer",
        "check_source": True,
        "description":  "Factual — lock-in (ELSS)",
    },
    {
        "query":        "What is the minimum SIP amount for Mirae Asset ELSS?",
        "expect_type":  "answer",
        "check_source": True,
        "description":  "Factual — minimum SIP (ELSS)",
    },
    {
        "query":        "What is the benchmark index for Mirae Asset Liquid Fund?",
        "expect_type":  "answer",
        "check_source": True,
        "description":  "Factual — benchmark (Liquid Fund)",
    },
    {
        "query":        "What is the riskometer rating of Mirae Asset Flexi Cap Fund?",
        "expect_type":  "answer",
        "check_source": True,
        "description":  "Factual — riskometer (Flexi Cap)",
    },

    # --- Guard rails — Phase 3 should block before reaching Phase 4 ---
    {
        "query":        "Should I invest in Mirae Asset Large Cap Fund?",
        "expect_type":  "refusal",
        "expect_reason": "advisory",
        "check_source": False,
        "description":  "Guard rail — advisory (should I invest)",
    },
    {
        "query":        "My PAN is ABCDE1234F. What is the exit load?",
        "expect_type":  "refusal",
        "expect_reason": "pii_pan",
        "check_source": False,
        "description":  "Guard rail — PII (PAN number)",
    },
    {
        "query":        "What is the current FD rate in SBI?",
        "expect_type":  "refusal",
        "expect_reason": "out_of_scope",
        "check_source": False,
        "description":  "Guard rail — out of scope (FD rate)",
    },
]

_ADVISORY_SIGNALS = ["recommend", "should invest", "suggest", "you should", "in my opinion"]


def _check_answer(result: dict, test: dict) -> tuple:
    """Returns (passed: bool, failures: list[str])."""
    failures = []
    t = result["type"]

    # Type check
    if t != test["expect_type"]:
        failures.append(f"expected type={test['expect_type']!r}, got {t!r}")
        return False, failures

    # Reason check (for refusals)
    if "expect_reason" in test:
        got_reason = result.get("reason", "")
        if got_reason != test["expect_reason"]:
            failures.append(f"expected reason={test['expect_reason']!r}, got {got_reason!r}")

    if t == "answer":
        text = result.get("text", "")
        # Non-empty answer
        if not text:
            failures.append("answer text is empty")
        # Source URL present
        if test["check_source"]:
            src = result.get("source_url", "")
            if not src:
                failures.append("source_url is empty")
            elif src not in text:
                failures.append(f"source URL not found in answer text")
        # No advisory language leaked
        text_lower = text.lower()
        for sig in _ADVISORY_SIGNALS:
            if sig in text_lower:
                failures.append(f"advisory signal '{sig}' found in answer")

    return len(failures) == 0, failures


def main():
    parser = argparse.ArgumentParser(description="Phase 4 end-to-end smoke tests")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    pipeline = Pipeline(verbose=args.verbose, generate=True)

    passed = 0
    failed = 0
    results = []

    print(f"Phase 4 End-to-End — {len(TESTS)} tests\n" + "=" * 60)

    for i, test in enumerate(TESTS, 1):
        result = pipeline.run(test["query"])
        ok, failures = _check_answer(result, test)

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        t = result["type"]
        print(f"[{status}] #{i:02d} {test['description']}")
        if t == "answer":
            text = result.get("text", "")
            model = result.get("model_used", "?")
            print(f"        model={model}  src={'✓' if result.get('source_url') else '✗'}")
            # Print first 120 chars of answer
            snippet = text.replace("\n", " ")[:120]
            print(f"        {snippet}{'...' if len(text) > 120 else ''}")
        elif t == "refusal":
            print(f"        reason={result.get('reason')!r}")
        else:
            print(f"        {result.get('message', '')[:100]}")

        for f in failures:
            print(f"        ↳ FAIL: {f}")
        print()

        results.append({
            "test":       test["description"],
            "query":      test["query"],
            "status":     status,
            "type":       t,
            "reason":     result.get("reason"),
            "model":      result.get("model_used"),
            "source_url": result.get("source_url"),
            "answer":     result.get("text", "")[:300],
            "failures":   failures,
        })

    print("=" * 60)
    print(f"Results: {passed}/{len(TESTS)} passed  ({failed} failed)")

    out = PROJECT_ROOT / "data" / "phase4_test_results.json"
    out.write_text(json.dumps({"passed": passed, "failed": failed, "tests": results}, indent=2))
    print(f"Detailed results → {out}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
