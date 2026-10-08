"""Testes da porta do cache de guidance de distribuição."""

from datetime import date
from decimal import Decimal

import flowscope.application.guidance_port as modulo
from flowscope.application.guidance_port import GuidanceStore
from flowscope.domain.fii import METODO_IA, AvaliacaoGuidance, Guidance

GUIDANCE = Guidance(
    valor_min=Decimal("0.85"),
    valor_max=Decimal("0.85"),
    periodo="2S26",
    data_relatorio=date(2026, 8, 1),
)

AVALIACAO = AvaliacaoGuidance(
    metodo=METODO_IA,
    data_relatorio=date(2026, 8, 1),
    guidance=GUIDANCE,
)


class _StoreFake:
    def __init__(self):
        self._dados: dict[tuple[str, str], AvaliacaoGuidance] = {}

    def obter(self, ticker):
        return next(
            (
                avaliacao.guidance
                for (t, _), avaliacao in self._dados.items()
                if t == ticker
            ),
            None,
        )

    def obter_avaliacao(self, ticker, chave):
        return self._dados.get((ticker, chave))

    def salvar_avaliacao(self, ticker, chave, avaliacao):
        self._dados[(ticker, chave)] = avaliacao


class TestPorta:
    def test_protocolo_expoe_leitura_e_gravacao(self):
        assert hasattr(GuidanceStore, "obter")
        assert hasattr(GuidanceStore, "obter_avaliacao")
        assert hasattr(GuidanceStore, "salvar_avaliacao")

    def test_implementacao_satisfaz_a_porta(self):
        store: GuidanceStore = _StoreFake()
        store.salvar_avaliacao("ALZR11", "a1b2", AVALIACAO)
        assert store.obter_avaliacao("ALZR11", "a1b2") == AVALIACAO
        assert store.obter("ALZR11") == GUIDANCE

    def test_modulo_nao_importa_infraestrutura(self):
        origens = {
            getattr(valor, "__module__", "")
            for valor in vars(modulo).values()
        }
        assert not any(
            origem.startswith("flowscope.infrastructure") for origem in origens
        )
