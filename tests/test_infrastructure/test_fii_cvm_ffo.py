from datetime import date
from decimal import Decimal

import pytest

from flowscope.domain.fii import FfoObservacao
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.cvm import (
    FONTE_CVM,
    CvmFiiAdapter,
    CvmSchemaError,
    parse_informe_mensal,
)
from flowscope.infrastructure.fii.ffo_provider import (
    FONTE_FUNDAMENTUS,
    FundamentusProvider,
    METODOLOGIA,
    extrair_ffo,
)

REFERENCIA = date(2026, 9, 4)
CNPJ = "12345678000195"


CSV_MENSAL = """CNPJ_FUNDO;DT_COMPTC;VL_PATRIM_LIQ;QUANT_COTA;NR_COTST
12345678000195;30/06/2026;2900000000,00;144000000;90000
12345678000195;31/07/2026;2920000000,00;144300000;98000
12345678000195;31/08/2026;2942000000,00;144355726;100000
12345678000195;30/09/2026;3000000000,00;145000000;110000
12345678000195;31/08/2026;9999999999,00;1;1
99999999000191;31/08/2026;1000000,00;1000;10
"""


class TestParseInformeMensal:
    def test_parse_linhas_validas(self):
        informes = parse_informe_mensal(CSV_MENSAL)
        assert len(informes) == 6

    def test_schema_invalido_levanta_erro(self):
        with pytest.raises(CvmSchemaError):
            parse_informe_mensal("CNPJ_FUNDO;VL_PATRIM_LIQ\n123;1\n")

    def test_conteudo_vazio_retorna_lista_vazia(self):
        assert parse_informe_mensal("") == []


class TestCvmFiiAdapter:
    def _adapter(self, cache: CacheManager | None = None) -> CvmFiiAdapter:
        def loader(ano: int) -> str:
            if ano == REFERENCIA.year:
                return CSV_MENSAL
            return ""

        return CvmFiiAdapter(
            loader=loader,
            resolver_cnpj=lambda ticker: CNPJ if ticker == "HGBS11" else None,
            cache=cache,
        )

    def test_seleciona_ultimo_informe_ate_a_referencia(self):
        patrimonio = self._adapter().patrimonio("HGBS11", REFERENCIA)
        assert patrimonio is not None
        assert patrimonio.net_asset_value == Decimal("2942000000.00")
        assert patrimonio.shares_outstanding == Decimal("144355726")
        assert patrimonio.cotistas == 100000
        assert patrimonio.reference_date == date(2026, 8, 31)
        assert patrimonio.fonte == FONTE_CVM

    def test_ignora_informe_com_competencia_futura(self):
        patrimonio = self._adapter().patrimonio("HGBS11", date(2026, 8, 15))
        assert patrimonio is not None
        assert patrimonio.reference_date == date(2026, 7, 31)

    def test_ticker_sem_cnpj_retorna_none(self):
        assert self._adapter().patrimonio("PETR4", REFERENCIA) is None

    def test_sem_informe_retorna_none(self):
        def loader(ano: int) -> str:
            return ""

        adapter = CvmFiiAdapter(loader=loader, resolver_cnpj=lambda _t: CNPJ)
        assert adapter.patrimonio("HGBS11", REFERENCIA) is None

    def test_falha_no_loader_retorna_none(self):
        def loader(ano: int) -> str:
            raise RuntimeError("boom")

        adapter = CvmFiiAdapter(loader=loader, resolver_cnpj=lambda _t: CNPJ)
        assert adapter.patrimonio("HGBS11", REFERENCIA) is None

    def test_loader_invocado_uma_vez_com_cache(self, tmp_path):
        chamadas: list[int] = []
        cache = CacheManager(cache_dir=tmp_path)

        def loader(ano: int) -> str:
            chamadas.append(ano)
            return CSV_MENSAL

        adapter = CvmFiiAdapter(
            loader=loader, resolver_cnpj=lambda _t: CNPJ, cache=cache
        )
        adapter.patrimonio("HGBS11", REFERENCIA)
        adapter.patrimonio("HGBS11", REFERENCIA)
        assert chamadas == [REFERENCIA.year]


HTML_FFO = """
<html><body><table class="fundamentus">
<tr><td>P/L</td><td>12,3</td></tr>
<tr><td>FFO últimos 12 meses</td><td>R$ 220.777.000</td></tr>
<tr><td>FFO últimos 3 meses</td><td>R$ 63.802.000</td></tr>
</table></body></html>
"""

HTML_SEM_FFO = "<html><body><p>Sem dados</p></body></html>"


class TestExtrairFfo:
    def test_extrai_ffo_12m_e_3m(self):
        ffo = extrair_ffo(HTML_FFO)
        assert ffo is not None
        assert ffo.ffo_12m == Decimal("220777000")
        assert ffo.ffo_3m == Decimal("63802000")
        assert ffo.fonte == FONTE_FUNDAMENTUS
        assert ffo.metodologia == METODOLOGIA

    def test_sem_ffo_retorna_none(self):
        assert extrair_ffo(HTML_SEM_FFO) is None

    def test_ffo_incompleto_retorna_none(self):
        html = (
            "<table><tr><td>FFO últimos 12 meses</td><td>R$ 1.000</td></tr></table>"
        )
        assert extrair_ffo(html) is None


class TestFundamentusProvider:
    def _provider(self, cache: CacheManager | None = None) -> FundamentusProvider:
        chamadas: list[str] = []
        loader = lambda ticker: (chamadas.append(ticker) or HTML_FFO)

        provider = FundamentusProvider(loader=loader, cache=cache)
        provider._chamadas = chamadas
        return provider

    def test_obter_ffo_do_ticker(self):
        ffo = self._provider().obter_ffo("HGBS11", REFERENCIA)
        assert isinstance(ffo, FfoObservacao)
        assert ffo.ffo_12m == Decimal("220777000")

    def test_loader_reutilizado_com_cache(self, tmp_path):
        provider = self._provider(cache=CacheManager(cache_dir=tmp_path))
        provider.obter_ffo("HGBS11", REFERENCIA)
        provider.obter_ffo("HGBS11", REFERENCIA)
        assert provider._chamadas == ["HGBS11"]

    def test_falha_no_loader_retorna_none(self):
        def loader(ticker: str) -> str:
            raise RuntimeError("boom")

        provider = FundamentusProvider(loader=loader)
        assert provider.obter_ffo("HGBS11", REFERENCIA) is None

    def test_ticker_sem_ffo_retorna_none(self):
        provider = FundamentusProvider(loader=lambda ticker: HTML_SEM_FFO)
        assert provider.obter_ffo("HGBS11", REFERENCIA) is None
