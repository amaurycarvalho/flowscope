"""Testes do bloco de conhecimento do próprio FlowScope."""

import pytest

from flowscope import __version__
from flowscope.presentation.gui.chat.conhecimento import montar_bloco_conhecimento
from flowscope.presentation.gui.widgets.about_panel import APRESENTACAO, LICENCA


@pytest.fixture
def bloco() -> str:
    """Bloco de conhecimento montado uma vez para os testes."""
    return montar_bloco_conhecimento()


class TestBlocoConhecimento:
    def test_contem_informacoes_da_aba_sobre(self, bloco):
        assert APRESENTACAO in bloco
        assert LICENCA in bloco
        assert f"v{__version__}" in bloco
        assert "Sobre o FlowScope" in bloco

    def test_contem_textos_de_orientacao_das_subabas(self, bloco):
        assert "Orientação das sub-abas" in bloco
        assert "VWAP — Volume Weighted Average Price" in bloco
        assert "Fundamentos — Métricas Fundamentalistas e Dividendos" in bloco

    def test_estavel_entre_chamadas(self, bloco):
        assert bloco == montar_bloco_conhecimento()
