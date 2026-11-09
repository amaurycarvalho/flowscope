"""Testes headless do registro da sub-aba Performance e da orientação."""

import re
from pathlib import Path
from types import SimpleNamespace

from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_tabs import TAB_CONTENT

_LAYOUT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "flowscope"
    / "presentation"
    / "gui"
    / "app_tab_layout.py"
)


def _ordem_subabas_gerais() -> list[str]:
    fonte = _LAYOUT.read_text(encoding="utf-8")
    return re.findall(r'_general_notebook\.add\(\s*\w+,\s*text="([^"]+)"', fonte)


class TestRegistroSubAba:
    def test_performance_entre_dominancia_e_rede(self):
        ordem = _ordem_subabas_gerais()
        assert ordem.index("Performance") == ordem.index("Dominância do Pregão") + 1
        assert ordem.index("Rede de Correlação") == ordem.index("Performance") + 1

    def test_resolucao_do_painel(self):
        painel = object()
        host = SimpleNamespace(
            _GENERAL={"Performance": painel},
            _TICKER={},
        )
        assert (
            ActionsMixin._resolve_chart(host, "Análise Geral", "Performance")
            is painel
        )


class TestOrientacao:
    def test_conteudo_da_orientacao(self):
        assert ("Análise Geral", "Performance") in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[("Análise Geral", "Performance")]
        texto = " ".join(parte for parte, _ in corpo)
        assert "Performance" in titulo
        assert "excesso de retorno" in texto.lower()
        assert "IFIX" in texto and "IBOV" in texto and "IDIV" in texto
        assert "split" in texto and "bonificação" in texto
        assert "não ajusta" in texto.lower() or "NÃO ajusta" in texto
        assert "ponto" in texto.lower() or "p.p." in texto


class TestIntegracaoCargaJobPainel:
    def test_simulado_gera_barras_combobox_e_aviso(self):
        from datetime import date
        from decimal import Decimal
        from unittest.mock import MagicMock

        from flowscope.application.performance import AnalyzePerformanceUseCase
        from flowscope.domain.index_history import IndexClose
        from flowscope.presentation.gui.charts.performance_panel import (
            AVISO_EVENTO,
            PerformanceFigure,
            PerformancePanel,
        )
        from flowscope.presentation.gui.controller_performance import (
            executar_performance,
        )

        d1, d2 = date(2026, 1, 5), date(2026, 1, 6)

        class Historico:
            series = {
                "IBOV": {d1: 100.0, d2: 100.0},
                "IDIV": {d1: 100.0, d2: 100.0},
                "IFIX": {d1: 100.0, d2: 100.0},
            }

            def get_index_history(self, index, start, end):
                return [
                    IndexClose(m, v) for m, v in sorted(self.series[index].items())
                ]

        class Cache:
            def __init__(self):
                self.store = {}

            def obter(self, chave):
                return self.store.get(chave.identidade())

            def registrar(self, chave, resultado):
                self.store[chave.identidade()] = resultado

        class Ctx:
            def raise_if_cancelled(self):
                pass

            def resultado(self, valor=None, **_):
                self.valor = valor

        current = {
            "PETR4": {"daily_data": [
                {"date": d1, "last_price": Decimal("10")},
                {"date": d2, "last_price": Decimal("5")},
            ]},
            "HGLG11": {"daily_data": [
                {"date": d1, "last_price": Decimal("10")},
                {"date": d2, "last_price": Decimal("10")},
            ]},
        }
        classificacao = {"PETR4": "ACAO", "HGLG11": "FII"}
        ctx = Ctx()
        executar_performance(
            ctx,
            AnalyzePerformanceUseCase(Historico()),
            Cache(),
            current,
            classificacao,
            list(classificacao),
            d2,
            SamplingConfig(30, "fibonacci"),
        )

        figura = PerformanceFigure()
        figura.update(ctx.valor)
        assert figura.benchmark_atual() == "IBOV"
        assert len(figura._bars) == 1
        assert AVISO_EVENTO in figura.hover_text(0)

        painel = PerformancePanel.__new__(PerformancePanel)
        painel._combo = MagicMock()
        painel._benchmark_var = MagicMock()
        painel._benchmark_var.get.return_value = ""
        painel._aplicar_combobox(ctx.valor)
        painel._benchmark_var.set.assert_called_once_with("IBOV")
        assert ("values", ["IFIX", "IBOV", "IDIV"]) in [
            call.args for call in painel._combo.__setitem__.call_args_list
        ]
