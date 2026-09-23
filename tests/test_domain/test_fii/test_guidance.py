"""Testes do value object de guidance e do campo em ``AnaliseFundamental``."""

from datetime import date
from decimal import Decimal

import flowscope.domain.fii as dominio
from flowscope.domain.fii import AnaliseFundamental, Guidance


def _guidance(minimo: str, maximo: str) -> Guidance:
    return Guidance(
        valor_min=Decimal(minimo),
        valor_max=Decimal(maximo),
        periodo="2S26",
        data_relatorio=date(2026, 8, 1),
    )


class TestGuidance:
    def test_valor_unico_tem_minimo_igual_ao_maximo(self):
        guidance = _guidance("0.85", "0.85")
        assert guidance.valor_min == guidance.valor_max == Decimal("0.85")

    def test_faixa_preserva_minimo_e_maximo(self):
        guidance = _guidance("0.74", "0.78")
        assert guidance.valor_min == Decimal("0.74")
        assert guidance.valor_max == Decimal("0.78")

    def test_caminho_pdf_e_opcional(self):
        assert _guidance("0.85", "0.85").caminho_pdf is None

    def test_exportado_pelo_pacote_de_dominio(self):
        assert dominio.Guidance is Guidance
        assert "Guidance" in dominio.__all__


class TestAnaliseFundamental:
    def test_guidance_default_e_none(self):
        assert "guidance" in AnaliseFundamental.__dataclass_fields__
        campo = AnaliseFundamental.__dataclass_fields__["guidance"]
        assert campo.default is None
