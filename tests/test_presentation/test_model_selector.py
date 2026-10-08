"""Testes das funções puras do seletor de modelo ativo.

A composição das opções e a escolha do item selecionado são puras e testadas
sem ``DISPLAY``; o widget é exercitado pelos testes de integração dos painéis.
"""

from flowscope.presentation.gui.llm.model_selector import (
    ROTULO_NONE,
    opcoes_modelo,
    selecao_modelo,
)


class TestOpcoesModelo:
    def test_none_e_ativos_na_ordem(self):
        assert opcoes_modelo(["deepseek", "gemini"], "deepseek") == [
            ROTULO_NONE,
            "deepseek",
            "gemini",
        ]

    def test_inclui_provedor_corrente_fora_dos_ativos(self):
        assert opcoes_modelo(["deepseek"], "openai") == [
            ROTULO_NONE,
            "deepseek",
            "openai",
        ]

    def test_nao_duplica_provedor_corrente_ativo(self):
        assert opcoes_modelo(["deepseek", "gemini"], "gemini") == [
            ROTULO_NONE,
            "deepseek",
            "gemini",
        ]

    def test_none_nao_duplica(self):
        assert opcoes_modelo([], "none") == [ROTULO_NONE]


class TestSelecaoModelo:
    def test_provider_presente_e_selecionado(self):
        assert selecao_modelo("deepseek", [ROTULO_NONE, "deepseek"]) == "deepseek"

    def test_provider_ausente_cai_em_none(self):
        assert selecao_modelo("openai", [ROTULO_NONE, "deepseek"]) == ROTULO_NONE

    def test_none_e_selecionado(self):
        assert selecao_modelo("none", [ROTULO_NONE, "deepseek"]) == ROTULO_NONE
