import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class ProgressStep:
    label: str
    current: int = 0
    total: int = 0
    weight: int = 1
    failures: int = 0


class ProgressReporter:
    def __init__(self, on_update: Callable[[int, int, str], None] | None = None):
        self._on_update = on_update
        self._phases: list[ProgressStep] = []
        self._current_phase: int = -1
        self._total_weight: int = 0
        self._completed_weight: int = 0
        self._last_pct: int = -1
        self._last_update_ms: float = 0
        self._throttle_pct: int = 1
        self._throttle_ms: float = 100

    def start_phase(self, label: str, total: int, weight: int = 1) -> None:
        self._phases.append(ProgressStep(label=label, total=total, weight=weight))
        self._total_weight += weight
        self._current_phase = len(self._phases) - 1

    def _phase(self) -> ProgressStep:
        return self._phases[self._current_phase]

    def advance(self, n: int = 1, detail: str = "") -> None:
        phase = self._phase()
        phase.current += n
        self._report(detail)

    def fail(self, n: int = 1, detail: str = "") -> None:
        phase = self._phase()
        phase.failures += n
        phase.current += n
        self._report(detail)

    def finish_phase(self, detail: str = "") -> None:
        phase = self._phase()
        phase.current = phase.total
        self._completed_weight += phase.weight
        self._report(detail)

    def _report(self, detail: str = "") -> None:
        if not self._on_update:
            return
        phase = self._phase()
        if phase.total > 0:
            phase_pct = phase.current / phase.total
        else:
            phase_pct = 1.0
        global_weight = self._completed_weight + phase_pct * phase.weight
        total_weight = max(self._total_weight, 1)
        pct = int(global_weight / total_weight * 100)

        now_ms = time.monotonic() * 1000
        if self._last_pct >= 0 and self._last_update_ms > 0:
            if (
                abs(pct - self._last_pct) < self._throttle_pct
                and now_ms - self._last_update_ms < self._throttle_ms
                and pct < 100
            ):
                return

        self._last_pct = pct
        self._last_update_ms = now_ms

        label = phase.label
        if phase.failures > 0:
            label += f" ({phase.failures} falha{'s' if phase.failures > 1 else ''})"
        if detail:
            label = f"{label} — {detail}"
        self._on_update(phase.current, phase.total, label)
