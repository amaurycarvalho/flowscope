"""Testes da porta do cache de guidance de distribuição."""

from datetime import date
from decimal import Decimal

import flowscope.application.guidance_port as modulo
from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.fii import Guidance

GUIDANCE = Guidance(
    valor_min=Decimal("0.85"),
    valor_max=Decimal("0.85"),
    periodo="2S26",
    data_relatorio=date(2026, 8, 1),
)


class _StoreFake:
    def __init__(self):
        self._dados: dict[str, Guidance] = {}

    def obter(self, ticker):
        return self._dados.get(ticker)

    def salvar(self, ticker, guidance):
        self._dados[ticker] = guidance


class TestPorta:
    def test_protocolo_expoe_leitura_e_gravacao(self):
        assert hasattr(GuidanceStore, "obter")
        assert hasattr(GuidanceStore, "salvar")

    def test_implementacao_satisfaz_a_porta(self):
        store: GuidanceStore = _StoreFake()
        store.salvar("ALZR11", GUIDANCE)
        assert store.obter("ALZR11") == GUIDANCE

    def test_modulo_nao_importa_infraestrutura(self):
        origens = {
            getattr(valor, "__module__", "")
            for valor in vars(modulo).values()
        }
        assert not any(
            origem.startswith("flowscope.infrastructure") for origem in origens
        )
