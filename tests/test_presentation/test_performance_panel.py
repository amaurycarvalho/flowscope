from unittest.mock import MagicMock

from flowscope.presentation.gui.charts.performance_panel import (
    AVISO_EVENTO,
    MENSAGEM_BENCHMARK_INDISPONIVEL,
    MENSAGEM_SEM_DADOS,
    MENSAGEM_SEM_ELEGIVEIS,
    PerformanceFigure,
    PerformancePanel,
)


def _payload(suspicious: bool = False) -> dict:
    return {
        "benchmarks": ["IFIX", "IBOV"],
        "default": "IBOV",
        "results": {
            "IBOV": {
                "benchmark": "IBOV",
                "index_available": True,
                "return_basis": "price",
                "tickers": [
                    {
                        "ticker": "PETR4",
                        "ticker_return": 0.12,
                        "index_return": 0.10,
                        "excess_pp": 2.0,
                        "observations": 3,
                        "suspicious_event": suspicious,
                    },
                    {
                        "ticker": "VALE3",
                        "ticker_return": 0.05,
                        "index_return": 0.10,
                        "excess_pp": -5.0,
                        "observations": 3,
                        "suspicious_event": False,
                    },
                ],
            }
        },
    }


class TestPerformanceFigure:
    def test_desenha_barras(self):
        figura = PerformanceFigure()
        figura.update(_payload())
        assert figura.benchmark_atual() == "IBOV"
        assert len(figura._bars) == 2
        assert "Excesso vs IBOV (p.p.)" in figura._ax.get_ylabel()
        assert not figura._empty_label.get_visible()

    def test_hover_com_retornos(self):
        figura = PerformanceFigure()
        figura.update(_payload())
        texto = figura.hover_text(0)
        assert "PETR4" in texto
        assert "+12,00%" in texto
        assert "+10,00%" in texto
        assert "+2,00 p.p." in texto
        assert AVISO_EVENTO not in texto

    def test_hover_com_aviso_de_evento(self):
        figura = PerformanceFigure()
        figura.update(_payload(suspicious=True))
        assert AVISO_EVENTO in figura.hover_text(0)

    def test_usa_benchmark_solicitado(self):
        figura = PerformanceFigure()
        figura.update(_payload(), benchmark="IFIX")
        assert figura.benchmark_atual() == "IFIX"

    def test_estado_vazio_sem_dados(self):
        figura = PerformanceFigure()
        figura.update({})
        assert figura._empty_label.get_visible()
        assert figura._empty_label.get_text() == MENSAGEM_SEM_DADOS

    def test_benchmark_indisponivel(self):
        figura = PerformanceFigure()
        payload = _payload()
        payload["results"]["IBOV"]["index_available"] = False
        figura.update(payload)
        assert figura._empty_label.get_text() == MENSAGEM_BENCHMARK_INDISPONIVEL

    def test_sem_tickers_elegiveis(self):
        figura = PerformanceFigure()
        payload = _payload()
        payload["results"]["IBOV"]["tickers"] = []
        figura.update(payload)
        assert figura._empty_label.get_text() == MENSAGEM_SEM_ELEGIVEIS

    def test_reset(self):
        figura = PerformanceFigure()
        figura.update(_payload())
        figura.reset()
        assert figura._empty_label.get_text() == MENSAGEM_SEM_DADOS

    def test_get_figure_para_copia(self):
        figura = PerformanceFigure()
        assert figura.get_figure() is figura._figure

    def test_excesso_invalido_nao_quebra(self, caplog):
        figura = PerformanceFigure()
        payload = _payload()
        payload["results"]["IBOV"]["tickers"][0]["excess_pp"] = "abc"
        figura.update(payload)
        assert len(figura._bars) == 2
        assert "excesso inválido" in caplog.text


class TestCombobox:
    def _panel(self) -> PerformancePanel:
        painel = PerformancePanel.__new__(PerformancePanel)
        painel._combo = MagicMock()
        painel._benchmark_var = MagicMock()
        painel._benchmark_var.get.return_value = ""
        return painel

    def test_opcoes_e_default(self):
        painel = self._panel()
        painel._aplicar_combobox(_payload())
        assert ("values", ["IFIX", "IBOV"]) in [
            call.args for call in painel._combo.__setitem__.call_args_list
        ]
        assert ("state", "readonly") in [
            call.args for call in painel._combo.__setitem__.call_args_list
        ]
        painel._benchmark_var.set.assert_called_once_with("IBOV")

    def test_default_pelo_payload(self):
        painel = self._panel()
        dados = _payload()
        dados["default"] = "IFIX"
        painel._aplicar_combobox(dados)
        painel._benchmark_var.set.assert_called_once_with("IFIX")

    def test_sem_opcoes_desabilita(self):
        painel = self._panel()
        painel._aplicar_combobox({"benchmarks": [], "default": None})
        assert ("state", "disabled") in [
            call.args for call in painel._combo.__setitem__.call_args_list
        ]
        painel._benchmark_var.set.assert_called_once_with("")
