"""Guarda de orçamento dos testes de UI gated por display.

Registra a contagem baseline de testes decorados com ``@needs_display`` e
reprova quando o número aumenta: o processamento deve ser testado headless e os
testes de UI ficam restritos a wiring, estado de widget, empty-state e o
marshaling real do pump até o widget.
"""

from pathlib import Path

_TESTS_APRESENTACAO = Path(__file__).resolve().parents[1] / "test_presentation"

#: Contagem baseline de decoradores ``@needs_display`` (não pode aumentar).
BASELINE_NEEDS_DISPLAY = 250


def _contar_needs_display() -> int:
    """Conta os decoradores ``@needs_display`` nos testes de apresentação."""
    return sum(
        caminho.read_text(encoding="utf-8").count("@needs_display")
        for caminho in _TESTS_APRESENTACAO.rglob("*.py")
    )


class TestOrcamentoTestesUI:
    """Verifica que o orçamento de testes de UI não regride."""

    def test_nao_aumenta_needs_display(self) -> None:
        """A contagem de testes gated por display não pode aumentar."""
        total = _contar_needs_display()
        assert total <= BASELINE_NEEDS_DISPLAY, (
            f"Testes de UI gated por display aumentaram: {total} > "
            f"{BASELINE_NEEDS_DISPLAY}. Migre o processamento para testes "
            "headless ou atualize a baseline de forma consciente."
        )
