#!/usr/bin/env python3
"""
Quality Gate enforcement script.
Executes each quality check as an external CLI tool, captures the metric value,
threshold, severity, status and evidence, and emits a consolidated report.
Exits non-zero when any blocking check fails or a tool errors (fail-loud).
"""

import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any


class QualityGate:
    def __init__(self, run_id: str = "", python_version: str = "") -> None:
        self.passed = True
        self.report: list[dict[str, Any]] = []
        self.run_id = run_id or os.environ.get("GITHUB_RUN_ID", "")
        self.python_version = python_version or os.environ.get("PYTHON_VERSION", "")

    def _record(
        self,
        name: str,
        value: str,
        threshold: str,
        severity: str,
        status: str,
        evidence: list[str] | None = None,
    ) -> None:
        if status == "fail" and severity == "blocking":
            self.passed = False
        self.report.append(
            {
                "name": name,
                "value": value,
                "threshold": threshold,
                "severity": severity,
                "status": status,
                "evidence": evidence or [],
            }
        )

    def record_mi(self, mi_text: str = "") -> None:
        """Record the Maintainability Index as its own metric row (Contract 2).

        Blocking when worst MI < 30, warning when 30 <= worst < 70, pass when
        worst >= 70. Fail-loud (FR-014) when MI cannot be established.
        """
        if not mi_text:
            mi_text = subprocess.run(
                [".venv/bin/radon", "mi", "-s", ".", "-i", "tests,build,dist,ccache,mutants,.venv"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout
        scores = [float(m) for m in re.findall(r"\(([\d.]+)\)\s*$", mi_text, re.MULTILINE)]
        if not scores:
            self._record(
                "Maintainability Index",
                value="unavailable",
                threshold=">= 30",
                severity="blocking",
                status="fail",
                evidence=["no modules evaluated; fail-loud"],
            )
            return
        worst = min(scores)
        if worst < 30:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 30",
                severity="blocking",
                status="fail",
            )
        elif worst < 70:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 70 but >= 30 to pass",
                severity="warning",
                status="warn",
            )
        else:
            self._record(
                "Maintainability Index",
                value=f"{worst:.1f}",
                threshold=">= 70",
                severity="informational",
                status="pass",
            )

    def run_command(self, cmd: list[str], name: str, threshold: str, severity: str) -> None:
        """Run a command; tool errors are recorded as a blocking failure."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                self._record(
                    name,
                    value=f"exit {result.returncode}",
                    threshold=threshold,
                    severity=severity,
                    status="fail",
                    evidence=(result.stderr or result.stdout).strip().splitlines()[:20],
                )
            else:
                self._record(name, value="ok", threshold=threshold, severity=severity, status="pass")
        except Exception as exc:
            self._record(
                name,
                value=f"error: {exc}",
                threshold=threshold,
                severity="blocking",
                status="fail",
                evidence=[str(exc)],
            )

    def summary(self) -> str:
        lines = ["=" * 50, "QUALITY GATE REPORT", "=" * 50]
        for check in self.report:
            mark = "PASS" if check["status"] == "pass" else "FAIL"
            lines.append(f"[{mark}] {check['name']}: {check['value']} (threshold {check['threshold']})")
            if check["evidence"]:
                lines.append(f"      evidence: {check['evidence'][0]}")
        lines.append("=" * 50)
        lines.append("All quality checks passed!" if self.passed else "Quality gate failed!")
        return "\n".join(lines)

    def json(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "python_version": self.python_version,
            "overall_status": "pass" if self.passed else "fail",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": self.report,
        }


def main() -> int:
    gate = QualityGate()

    gate.run_command(["make", "lint"], "lint", "no violations", "blocking")
    gate.run_command(["make", "complexity"], "complexity", "< 10 CCN", "blocking")
    gate.record_mi()
    gate.run_command(["make", "duplication"], "duplication", "< 10%", "blocking")
    gate.run_command(["make", "test"], "coverage", ">= 85%", "blocking")
    gate.run_command(["make", "mutation-check"], "mutation", ">= 80% score", "blocking")
    gate.run_command(["make", "security"], "security", "no ERROR findings", "blocking")

    print(gate.summary())
    print(json.dumps(gate.json(), indent=2))

    return 0 if gate.passed else 1


if __name__ == "__main__":
    sys.exit(main())
