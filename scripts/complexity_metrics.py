#!/usr/bin/env python3
"""
Complexity metrics script.

Runs `radon mi` and `radon hal` over the source package and enforces the
Maintainability Index contract (Contract 2):

- worst MI >= 70 -> pass (exit 0)
- 30 <= worst MI < 70 -> warning (exit 0)
- worst MI < 30 -> blocking (exit 1)
- empty/unparseable MI -> blocking (exit 1), fail-loud

Halstead metrics are reported as informational only and never fail the gate.
"""

import re
import subprocess
import sys
from typing import Any

SRC = "src"
IGNORES = "tests,build,dist,ccache,mutants,.venv,.opencode"
MI_BLOCKING = 30
MI_PASS = 70


def run_radon(args: list[str]) -> str:
    result = subprocess.run(
        [".venv/bin/radon", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr or result.stdout)
        sys.exit(1)
    return result.stdout


def parse_mi(text: str) -> list[float]:
    scores = [float(m) for m in re.findall(r"\(([\d.]+)\)\s*$", text, re.MULTILINE)]
    return scores


def enforce_mi(scores: list[float]) -> int:
    if not scores:
        print("[FAIL] Maintainability Index: unavailable (fail-loud)")
        return 1
    worst = min(scores)
    if worst < MI_BLOCKING:
        print(f"[FAIL] Maintainability Index: {worst:.1f} < {MI_BLOCKING} (blocking)")
        return 1
    if worst < MI_PASS:
        print(f"[WARN] Maintainability Index: {worst:.1f} (30-70, non-blocking)")
        return 0
    print(f"[PASS] Maintainability Index: {worst:.1f} >= {MI_PASS}")
    return 0


def report_halstead(text: str) -> None:
    print("\n--- Halstead metrics (informational) ---")
    for line in text.splitlines():
        if "total" in line.lower() or ":" not in line:
            print(line)
        else:
            print(line)


def main() -> int:
    print("=== Maintainability Index ===")
    mi_text = run_radon(["mi", "-s", SRC, "-i", IGNORES])
    print(mi_text)
    mi_status = enforce_mi(parse_mi(mi_text))

    hal_text = run_radon(["hal", SRC])
    report_halstead(hal_text)

    return mi_status


if __name__ == "__main__":
    sys.exit(main())
