"""Testes do mapeamento de dados do painel de rede de correlação."""

from datetime import date, timedelta
from decimal import Decimal

from flowscope.application.network.dados import (
    MENSAGEM_POUCAS_OBS,
    MENSAGEM_SEM_TICKERS,
    extrair_series,
    formatar_correlacao,
    formatar_half_life,
    formatar_modularidade,
    mensagem_indisponivel,
    rotulo_diagnostico,
)
from flowscope.domain.network_analysis import (
    SamplingDiagnostics,
    analyze_network,
)

BASE = date(2025, 1, 1)


def _dia(offset: int, preco: str) -> dict:
    return {"date": BASE + timedelta(days=offset), "last_price": Decimal(preco)}


class TestExtrairSeries:
    def test_extrai_series_ordenadas(self):
        current = {
            "PETR4": {"daily_data": [_dia(2, "12"), _dia(0, "10"), _dia(1, "11")]},
        }
        dados = extrair_series(current)
        assert list(dados.series) == ["PETR4"]
        assert dados.series["PETR4"] == (
            (BASE, 10.0),
            (BASE + timedelta(days=1), 11.0),
            (BASE + timedelta(days=2), 12.0),
        )
        assert dados.sem_dados == ()

    def test_descarta_preco_ausente_ou_nao_positivo(self):
        current = {
            "PETR4": {
                "daily_data": [
                    _dia(0, "10"),
                    {"date": BASE + timedelta(days=1), "last_price": None},
                    _dia(2, "0"),
                    {"date": BASE + timedelta(days=3), "last_price": "abc"},
                    {"last_price": Decimal("5")},
                    _dia(4, "12"),
                ]
            },
        }
        dados = extrair_series(current)
        assert dados.series["PETR4"] == (
            (BASE, 10.0),
            (BASE + timedelta(days=4), 12.0),
        )

    def test_ticker_sem_dados_reportado(self):
        current = {
            "PETR4": {"daily_data": [_dia(0, "10")]},
            "VALE3": {"daily_data": []},
        }
        dados = extrair_series(current, ["PETR4", "VALE3", "XXXX"])
        assert list(dados.series) == ["PETR4"]
        assert dados.sem_dados == ("VALE3", "XXXX")

    def test_info_invalida_conta_como_sem_dados(self):
        dados = extrair_series({"PETR4": None}, ["PETR4"])
        assert dados.series == {}
        assert dados.sem_dados == ("PETR4",)

    def test_sem_tickers_retorna_vazio(self):
        dados = extrair_series({}, [])
        assert dados.series == {}
        assert dados.sem_dados == ()


class TestFormatadores:
    def test_formatar_correlacao(self):
        assert formatar_correlacao(0.723) == "+0,72"
        assert formatar_correlacao(-0.5) == "-0,50"

    def test_formatar_half_life(self):
        assert formatar_half_life(3.4, 5.0) == "3,4 obs (~5,0 dias úteis)"
        assert formatar_half_life(2.0, None) == "2,0 obs"
        assert formatar_half_life(None, None) == "sem reversão"

    def test_formatar_modularidade(self):
        assert formatar_modularidade(0.42) == "modularidade 0,42"

    def test_rotulo_diagnostico(self):
        diag = SamplingDiagnostics(40, 90, 1, 2.0, 5)
        assert rotulo_diagnostico(diag) == (
            "40 observações · 90 dias corridos · gaps 1/2,0/5 dias úteis"
        )

    def test_rotulo_diagnostico_vazio(self):
        assert rotulo_diagnostico(SamplingDiagnostics(0, 0, 0, 0.0, 0)) == (
            "Sem observações alinhadas"
        )


class TestMensagemIndisponivel:
    def _resultado(self, current: dict):
        dados = extrair_series(current)
        return dados, analyze_network(dados.series)

    def test_sem_dados_carregados(self):
        dados, resultado = self._resultado({"PETR4": {"daily_data": []}})
        assert mensagem_indisponivel(dados, resultado) == (
            "Sem dados carregados para os tickers selecionados"
        )

    def test_sem_tickers_suficientes(self):
        dados, resultado = self._resultado({"PETR4": {"daily_data": [_dia(0, "10")]}})
        assert mensagem_indisponivel(dados, resultado) == MENSAGEM_SEM_TICKERS

    def test_poucas_observacoes(self):
        dias = {
            ticker: {
                "daily_data": [_dia(i, str(10 + i)) for i in range(10)]
            }
            for ticker in ("PETR4", "VALE3")
        }
        dados, resultado = self._resultado(dias)
        assert mensagem_indisponivel(dados, resultado) == MENSAGEM_POUCAS_OBS
