import subprocess
import sys
import textwrap
from pathlib import Path

from flowscope.infrastructure.cache import CacheManager
from flowscope.presentation.composicao import Nucleo, montar_nucleo

_SCRIPT_SEM_TK = textwrap.dedent(
    """
    import sys
    import tempfile
    from pathlib import Path

    class BloqueioTk:
        def find_spec(self, nome, caminho, alvo=None):
            if nome == "tkinter" or nome.startswith("tkinter."):
                raise ImportError("tkinter bloqueado no teste")
            return None

    sys.meta_path.insert(0, BloqueioTk())
    sys.modules.pop("tkinter", None)

    from flowscope.infrastructure.cache import CacheManager
    from flowscope.presentation.composicao import montar_nucleo

    tmp = Path(tempfile.mkdtemp())
    nucleo = montar_nucleo(CacheManager(cache_dir=tmp))
    assert nucleo.documentos is not None
    assert nucleo.noticias is not None
    assert nucleo.aquisicao_documentos is not None
    assert nucleo.aquisicao_noticias is not None
    assert nucleo.renda_fixa.aquisicao is not None
    assert nucleo.renda_fixa.consulta is not None
    assert nucleo.renda_fixa.inferencias is not None
    assert nucleo.renda_fixa.inferencia is not None
    assert nucleo.history_store is not None
    assert nucleo.guidance_store is not None
    assert "tkinter" not in sys.modules
    print("OK")
    """
)


class TestMontarNucleo:
    def test_monta_grafo_com_cache_customizado(self, tmp_path):
        nucleo = montar_nucleo(CacheManager(cache_dir=tmp_path))
        assert isinstance(nucleo, Nucleo)
        assert nucleo.base == tmp_path
        assert nucleo.documentos.catalogo is not None
        assert nucleo.noticias.catalogo is not None
        assert nucleo.renda_fixa.consulta is not None
        assert nucleo.renda_fixa.inferencia is not None
        assert callable(nucleo.renda_fixa.paths)
        assert callable(nucleo.llm_factory)
        assert callable(nucleo.deduplicar_documentos)
        assert callable(nucleo.resolver_fiagro)
        assert nucleo.performance_cache is not None
        assert nucleo.performance_use_case is not None

    def test_monta_grafo_sem_tk(self):
        resultado = subprocess.run(
            [sys.executable, "-c", _SCRIPT_SEM_TK],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().endswith("OK")

    def test_mercado_factory(self, tmp_path):
        from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult

        nucleo = montar_nucleo(CacheManager(cache_dir=tmp_path))
        assert nucleo.mercado_factory is B3MarketPriceFromResult

    def test_store_de_identidade_injetado_e_compartilhado(self, tmp_path, monkeypatch):
        from flowscope.domain.b3 import B3Fund
        from flowscope.infrastructure.b3.fund_identity_store import (
            JsonFundIdentityStore,
        )
        from flowscope.infrastructure.fii.cvm_fund_data_provider import (
            CvmAnnualFundDataProvider,
            CvmIndexadoresProvider,
        )

        nucleo = montar_nucleo(CacheManager(cache_dir=tmp_path))
        assert isinstance(nucleo.b3_fund_identity_store, JsonFundIdentityStore)
        assert nucleo.b3_fund_identity_store.caminho("ALZR11") == (
            tmp_path / "fund_identity" / "ALZR11.json"
        )
        assert nucleo.b3_fund_repository._identity_store is (
            nucleo.b3_fund_identity_store
        )

        fundo = B3Fund(
            ticker="ALZR11",
            fnet_id="20294",
            primary_id="870",
            name="ALIANZA TRUST",
            trading_name="28.737.771/0001-85",
        )
        monkeypatch.setattr(
            nucleo.b3_fund_repository, "find_by_ticker", lambda _ticker: fundo
        )
        annual = next(
            provider
            for provider in nucleo.fundamental_provider.providers
            if isinstance(provider, CvmAnnualFundDataProvider)
        )
        indexadores = nucleo.fundamental_indexadores_provider
        assert isinstance(indexadores, CvmIndexadoresProvider)
        assert annual._resolver("ALZR11").cnpj_fundo_classe == "28737771000185"
        assert indexadores._resolver("ALZR11").cnpj_fundo_classe == (
            "28737771000185"
        )
