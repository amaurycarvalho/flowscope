"""Testes do contexto de fundamentos do chat (escopo e serialização)."""

import pytest

from flowscope.presentation.gui.chat.fundamentos import (
    ORIENTACAO_SEM_DADOS,
    montar_contexto_fundamentos,
    serializar_fundamentos,
    tickers_do_escopo,
)


@pytest.fixture
def dados() -> dict:
    """Fundamentos sintéticos de três tickers para os cenários de escopo."""
    return {"PETR4": None, "VALE3": None, "ITUB4": None}


class TestSerializacao:
    def test_uma_linha_por_ticker(self):
        texto = serializar_fundamentos({"PETR4": None, "VALE3": None}, ["PETR4", "VALE3"])
        linhas = texto.splitlines()
        assert len(linhas) == 2
        assert linhas[0].startswith("[PETR4]")
        assert linhas[1].startswith("[VALE3]")

    def test_ticker_ausente_omitido(self):
        assert serializar_fundamentos({"PETR4": None}, ["PETR4", "XPTO"]) == (
            serializar_fundamentos({"PETR4": None}, ["PETR4"])
        )

    def test_sem_tickers_retorna_vazio(self):
        assert serializar_fundamentos({}, []) == ""


class TestEscopo:
    def test_watchlist_completa_sem_ticker(self, dados):
        escopo = tickers_do_escopo(dados, None, ["PETR4", "VALE3", "ITUB4"])
        assert escopo == ["PETR4", "VALE3", "ITUB4"]

    def test_ticker_informado_restringe_escopo(self, dados):
        assert tickers_do_escopo(dados, "VALE3", ["PETR4", "VALE3"]) == ["VALE3"]

    def test_ticker_ausente_fica_vazio(self, dados):
        assert tickers_do_escopo(dados, "XPTO", ["PETR4"]) == []


class TestContexto:
    def test_watchlist_completa(self, dados):
        texto = montar_contexto_fundamentos(dados, None, ["PETR4", "VALE3"])
        assert "[PETR4]" in texto
        assert "[VALE3]" in texto
        assert "[ITUB4]" not in texto

    def test_ticker_informado_apenas(self, dados):
        texto = montar_contexto_fundamentos(dados, "ITUB4", ["PETR4", "VALE3"])
        assert "[ITUB4]" in texto
        assert "[PETR4]" not in texto

    def test_sem_dados_orienta_carregamento(self):
        assert montar_contexto_fundamentos({}, None, []) == ORIENTACAO_SEM_DADOS
        assert "carregue os dados" in ORIENTACAO_SEM_DADOS

    def test_escopo_vazio_orienta_carregamento(self, dados):
        texto = montar_contexto_fundamentos(dados, "XPTO", ["PETR4"])
        assert texto == ORIENTACAO_SEM_DADOS
