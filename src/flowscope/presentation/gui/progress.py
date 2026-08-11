"""Relatório de progresso das operações longas da interface gráfica.

O módulo concentra a lógica de acompanhamento de fases ponderadas por
peso, permitindo que operações longas da interface reportem seu avanço
de forma uniforme e controlada por limites de frequência.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ProgressStep:
    """Representa uma etapa de progresso com peso na barra global.

    Attributes:
        label: Rótulo exibido para a etapa em andamento.
        current: Quantidade de unidades já processadas na etapa.
        total: Quantidade total de unidades esperada na etapa.
        weight: Peso relativo da etapa na barra global de progresso.
        failures: Número de falhas registradas durante a etapa.
    """

    label: str
    current: int = 0
    total: int = 0
    weight: int = 1
    failures: int = 0


class ProgressReporter:
    """Relata o progresso de fases ponderadas por peso ao chamador.

    O relator acumula fases iniciadas por :meth:`start_phase` e notifica
    o progresso por meio do callback ``on_update``, respeitando limites
    de frequência para evitar atualizações excessivas da interface.
    """

    def __init__(
        self: "ProgressReporter",
        on_update: Callable[[int, int, str], None] | None = None,
    ) -> None:
        """Inicializa o relator de progresso com o callback de atualização."""
        self._on_update = on_update
        self._phases: list[ProgressStep] = []
        self._current_phase: int = -1
        self._total_weight: int = 0
        self._completed_weight: int = 0
        self._last_pct: int = -1
        self._last_update_ms: float = 0
        self._throttle_pct: int = 1
        self._throttle_ms: float = 100

    def start_phase(self: "ProgressReporter", label: str, total: int, weight: int = 1) -> None:
        """Inicia uma nova fase de progresso com rótulo, total e peso."""
        self._phases.append(ProgressStep(label=label, total=total, weight=weight))
        self._total_weight += weight
        self._current_phase = len(self._phases) - 1

    def _phase(self: "ProgressReporter") -> ProgressStep:
        """Retorna a etapa de progresso atualmente em andamento."""
        return self._phases[self._current_phase]

    def advance(self: "ProgressReporter", n: int = 1, detail: str = "") -> None:
        """Avança o progresso da fase atual em ``n`` unidades."""
        phase = self._phase()
        phase.current += n
        self._report(detail)

    def fail(self: "ProgressReporter", n: int = 1, detail: str = "") -> None:
        """Registra uma falha e avança o progresso da fase atual."""
        phase = self._phase()
        phase.failures += n
        phase.current += n
        self._report(detail)

    def finish_phase(self: "ProgressReporter", detail: str = "") -> None:
        """Marca a fase atual como concluída e soma seu peso ao total."""
        phase = self._phase()
        phase.current = phase.total
        self._completed_weight += phase.weight
        self._report(detail)

    def _report(self: "ProgressReporter", detail: str = "") -> None:
        """Notifica o callback com o percentual global de progresso."""
        if not self._on_update:
            return
        phase = self._phase()
        phase_pct = self._phase_percentage(phase)
        global_weight = self._completed_weight + phase_pct * phase.weight
        total_weight = max(self._total_weight, 1)
        pct = int(global_weight / total_weight * 100)
        now_ms = time.monotonic() * 1000

        if not self._should_report(pct, now_ms):
            return

        self._last_pct = pct
        self._last_update_ms = now_ms
        label = self._build_label(phase, detail)
        self._on_update(phase.current, phase.total, label)

    def _phase_percentage(self: "ProgressReporter", phase: ProgressStep) -> float:
        """Calcula o percentual concluído da fase, assumindo 100% se total for zero."""
        if phase.total > 0:
            return phase.current / phase.total
        return 1.0

    def _should_report(self: "ProgressReporter", pct: int, now_ms: float) -> bool:
        """Verifica se a atualização deve ser notificada dado o limite de frequência."""
        if self._last_pct < 0:
            return True
        if self._last_update_ms <= 0:
            return True
        if abs(pct - self._last_pct) >= self._throttle_pct:
            return True
        if now_ms - self._last_update_ms >= self._throttle_ms:
            return True
        return pct >= 100

    def _build_label(self: "ProgressReporter", phase: ProgressStep, detail: str) -> str:
        """Compõe o rótulo da fase incluindo falhas e detalhe opcional."""
        label = phase.label
        if phase.failures > 0:
            plural = "s" if phase.failures > 1 else ""
            label = f"{label} ({phase.failures} falha{plural})"
        if detail:
            label = f"{label} — {detail}"
        return label
