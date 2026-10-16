"""Testes dos subcomandos CLI de ação e do lock global de ação."""

import argparse
import json
import threading
import time

import pytest

from flowscope.infrastructure.action_lock import ActionLock
from flowscope.presentation import cli_acoes, cli_resumos


class _FakeAquisicaoDocumentos:
    def __init__(self, desfecho=None, erro=False):
        self._desfecho = desfecho
        self._erro = erro
        self.chamadas: list[str] = []

    def adquirir(self, ticker, reference_date, progress=None, cancel_token=None):
        self.chamadas.append(ticker)
        if self._erro:
            raise RuntimeError("falha de aquisição")
        return self._desfecho


class _FakeAquisicaoNoticias:
    def __init__(self, adquiridos=3):
        self._adquiridos = adquiridos
        self.chamadas = 0

    def adquirir(self, reference_date, progress=None, cancel_token=None, palavra=None):
        self.chamadas += 1
        return self._adquiridos


class _FakeNucleo:
    def __init__(self, documentos=None, noticias=None):
        self.aquisicao_documentos = documentos
        self.aquisicao_noticias = noticias
        self.dedup: list = []

    def deduplicar_documentos(self, ticker, token):
        self.dedup.append(("doc", ticker))

    def deduplicar_noticias(self, token):
        self.dedup.append(("not", token))


class _Desfecho:
    def __init__(self, novos=0, reutilizados=0, falhas=0):
        self.novos = novos
        self.reutilizados = reutilizados
        self.falhas = falhas

    @property
    def adquiridos(self):
        return self.novos + self.reutilizados


class TestCarregarWatchlist:
    def test_arquivo_valido_normaliza_e_persiste(self, tmp_path, monkeypatch):
        arquivo = tmp_path / "tickers.txt"
        arquivo.write_text(" petr4 \nVale3\n\n", encoding="utf-8")
        capturado = {}
        monkeypatch.setattr(
            cli_acoes, "gravar_config", lambda chaves: capturado.update(chaves)
        )
        resultado = cli_acoes.carregar_watchlist(str(arquivo))
        assert resultado["tickers"] == ["PETR4", "VALE3"]
        assert capturado["last_tickers"] == ["PETR4", "VALE3"]
        assert capturado["last_ticker_file"] == str(arquivo.resolve())

    def test_arquivo_inexistente(self, tmp_path):
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.carregar_watchlist(str(tmp_path / "nao.txt"))
        assert exc.value.motivo == "arquivo_inexistente"

    def test_arquivo_vazio(self, tmp_path):
        arquivo = tmp_path / "vazio.txt"
        arquivo.write_text("   \n\n", encoding="utf-8")
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.carregar_watchlist(str(arquivo))
        assert exc.value.motivo == "watchlist_vazia"


class TestAtualizarDocumentos:
    def test_ticker_na_watchlist(self, monkeypatch):
        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: ["PETR4"])
        nucleo = _FakeNucleo(documentos=_FakeAquisicaoDocumentos(_Desfecho(novos=2)))
        monkeypatch.setattr(
            "flowscope.presentation.composicao.montar_nucleo", lambda: nucleo
        )
        from datetime import date

        resultado = cli_acoes.atualizar_documentos(date(2026, 10, 14), "PETR4")
        assert resultado["resultados"] == {"PETR4": "atualizado"}

    def test_ticker_fora_da_watchlist(self, monkeypatch):
        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: ["PETR4"])
        from datetime import date

        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.atualizar_documentos(date(2026, 10, 14), "VALE3")
        assert exc.value.motivo == "ticker_fora_watchlist"

    def test_sem_ticker_itera_watchlist(self, monkeypatch):
        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: ["PETR4", "VALE3"])
        fake = _FakeAquisicaoDocumentos(_Desfecho(novos=1))
        nucleo = _FakeNucleo(documentos=fake)
        monkeypatch.setattr(
            "flowscope.presentation.composicao.montar_nucleo", lambda: nucleo
        )
        from datetime import date

        resultado = cli_acoes.atualizar_documentos(date(2026, 10, 14))
        assert set(resultado["resultados"]) == {"PETR4", "VALE3"}
        assert fake.chamadas == ["PETR4", "VALE3"]

    def test_falha_parcial_marca_falha_e_nao_aborta(self, monkeypatch):
        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: ["PETR4", "VALE3"])
        fake = _FakeAquisicaoDocumentos(_Desfecho(novos=1))
        estado = {"primeiro": True}
        original = fake.adquirir

        def adquirir(ticker, reference_date, progress=None, cancel_token=None):
            if ticker == "PETR4":
                raise RuntimeError("falha")
            return original(ticker, reference_date, progress, cancel_token)

        fake.adquirir = adquirir
        nucleo = _FakeNucleo(documentos=fake)
        monkeypatch.setattr(
            "flowscope.presentation.composicao.montar_nucleo", lambda: nucleo
        )
        from datetime import date

        resultado = cli_acoes.atualizar_documentos(date(2026, 10, 14))
        assert resultado["resultados"]["PETR4"] == "falha"
        assert resultado["resultados"]["VALE3"] == "atualizado"
        assert resultado["falha"] is True

    def test_sem_watchlist_sem_ticker(self, monkeypatch):
        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: [])
        from datetime import date

        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.atualizar_documentos(date(2026, 10, 14))
        assert exc.value.motivo == "watchlist_ausente"


class TestAtualizarNoticias:
    def test_adquire_e_deduplica(self, monkeypatch):
        fake = _FakeAquisicaoNoticias(adquiridos=5)
        nucleo = _FakeNucleo(noticias=fake)
        monkeypatch.setattr(
            "flowscope.presentation.composicao.montar_nucleo", lambda: nucleo
        )
        from datetime import date

        resultado = cli_acoes.atualizar_noticias(date(2026, 10, 14))
        assert resultado["adquiridos"] == 5
        assert fake.chamadas == 1


class TestExecutarAcaoLock:
    def _args(self, **kwargs):
        base = {"comando": "carregar", "recurso": "watchlist", "pretty": False, "esperar": 0.0}
        base.update(kwargs)
        return argparse.Namespace(**base)

    def test_lock_em_uso_falha_com_erro_estruturado(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(cli_acoes, "ActionLock", lambda: ActionLock(tmp_path / "l"))
        monkeypatch.setattr(cli_acoes, "_despachar_acao", lambda args: {"ok": True})
        segurou = threading.Event()
        soltar = threading.Event()

        def segurar():
            ActionLock(tmp_path / "l").adquirir()
            segurou.set()
            soltar.wait(timeout=5)

        thread = threading.Thread(target=segurar)
        thread.start()
        assert segurou.wait(timeout=5)
        try:
            with pytest.raises(SystemExit) as exc:
                cli_acoes.executar_acao(self._args())
            assert exc.value.code == 1
        finally:
            soltar.set()
            thread.join(timeout=5)
        saida = json.loads(capsys.readouterr().out)
        assert saida["erro"]["motivo"] == "operacao_em_andamento"

    def test_erro_de_dominio_vira_json_e_codigo_1(self, capsys, monkeypatch):
        class _LockNulo:
            def adquirir(self, esperar=0.0):
                return self

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        def despachar(args):
            raise cli_acoes.AcaoError("watchlist_vazia", "x")

        monkeypatch.setattr(cli_acoes, "ActionLock", _LockNulo)
        monkeypatch.setattr(cli_acoes, "_despachar_acao", despachar)
        with pytest.raises(SystemExit) as exc:
            cli_acoes.executar_acao(self._args(recurso="watchlist"))
        assert exc.value.code == 1
        saida = json.loads(capsys.readouterr().out)
        assert saida["erro"]["motivo"] == "watchlist_vazia"


class _FakeCasoFundamental:
    houve_falha_recuperavel = False

    def execute(self, *args, **kwargs):
        return [object()]


class TestAtualizarFundamentos:
    def test_executa_mercado_e_fundamentos_e_registra(self, monkeypatch):
        from datetime import date

        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: ["PETR4"])

        class _Analyze:
            def execute(self, data, watchlist, config=None, **kw):
                return {"PETR4": {"daily_data": []}}

        nucleo = argparse.Namespace(analyze=_Analyze())
        monkeypatch.setattr(
            cli_acoes, "_montar_caso_fundamental", lambda n, m: _FakeCasoFundamental()
        )
        marcados = []
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        monkeypatch.setattr(
            comp, "registrar_carga_fundamentos", lambda d: marcados.append(d)
        )
        resultado = cli_acoes.atualizar_fundamentos(date(2026, 10, 14))
        assert resultado["processados"] == 1
        assert marcados == [date(2026, 10, 14)]

    def test_sem_watchlist(self, monkeypatch):
        from datetime import date

        monkeypatch.setattr(cli_acoes, "last_tickers", lambda: [])
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.atualizar_fundamentos(date(2026, 10, 14))
        assert exc.value.motivo == "watchlist_ausente"


class _NoticiasFake:
    def __init__(self, disponivel=False, catalogo=None, text_store=None,
                 summary_service=None, baixar_vinculo=None):
        self._disponivel = disponivel
        self.catalogo = catalogo
        self.text_store = text_store
        self.summary_service = summary_service
        self.baixar_vinculo = baixar_vinculo

    def llm_available(self):
        return self._disponivel


class _DocumentosFake:
    def __init__(self, disponivel=False):
        self._disponivel = disponivel
        self.summary_service = object()
        self.text_store = object()
        self.guidance_service = object()

    def llm_available(self):
        return self._disponivel


class TestResumir:
    def test_resumir_documentos_sem_llm(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: ["PETR4"])
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=False))
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_documentos("PETR4")
        assert exc.value.motivo == "llm_nao_configurada"

    def test_resumir_documentos_ticker_fora_watchlist(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: ["PETR4"])
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_documentos("VALE3")
        assert exc.value.motivo == "ticker_fora_watchlist"

    def test_resumir_documentos_sem_pendentes(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: ["PETR4"])
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=True))
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        monkeypatch.setattr(cli_resumos, "_pendentes_documentos", lambda n, t: [])
        resultado = cli_acoes.resumir_documentos("PETR4")
        assert resultado["pendentes"] == 0

    def test_resumir_noticias_sem_llm(self, monkeypatch):
        nucleo = argparse.Namespace(noticias=_NoticiasFake(disponivel=False))
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_noticias()
        assert exc.value.motivo == "llm_nao_configurada"
