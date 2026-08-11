#!/usr/bin/env python3
"""
Script to check mutation score from mutmut-cicd-stats.json file
"""

import json
import sys
from pathlib import Path

THRESHOLD = 80
JSON_FILE = Path("mutants/mutmut-cicd-stats.json")


def load_mutation_stats(json_path: Path) -> dict:
    """Load mutation statistics from JSON file."""
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        sys.exit(1)


def calculate_mutation_score(stats: dict) -> tuple[float, int, int]:
    """
    Calculate mutation score.

    Returns: (score, killed, total)
    """
    killed = stats.get('killed', 0)
    survived = stats.get('survived', 0)
    timeout = stats.get('timeout', 0)
    suspicious = stats.get('suspicious', 0)

    total = killed + survived + timeout + suspicious

    if total == 0:
        print("No mutants generated.")
        sys.exit(1)

    score = (killed / total) * 100
    return score, killed, total


def main() -> None:
    """Main function of the script."""
    stats = load_mutation_stats(JSON_FILE)

    print(f"Killed: {stats.get('killed', 0)}")
    print(f"Survived: {stats.get('survived', 0)}")
    print(f"Timeout: {stats.get('timeout', 0)}")
    print(f"Suspicious: {stats.get('suspicious', 0)}")
    print(f"Total: {stats.get('total', 0)}")
    print()

    score, killed, total = calculate_mutation_score(stats)

    print(f"Mutation Score: {score:.2f}%")

    if score >= THRESHOLD:
        print(f"Mutation Score >= {THRESHOLD}%")
        sys.exit(0)
    else:
        print(f"Mutation Score < {THRESHOLD}%")
        sys.exit(1)


if __name__ == "__main__":
    main()
