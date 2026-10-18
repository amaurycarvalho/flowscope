"""Testes dos subcomandos CLI de ação e do lock global de ação."""

import argparse
import json
import threading
import time
from datetime import date

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


class TestDataEfetiva:
    def test_sem_data_usa_hoje(self):
        assert cli_acoes._data_efetiva(None) == date.today()

    def test_data_explicita_tem_precedencia(self):
        assert cli_acoes._data_efetiva(date(2026, 10, 14)) == date(2026, 10, 14)


class TestDespachoAtualizar:
    def test_sem_data_usa_hoje_sem_consultar_referencia(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(
            cli_acoes,
            "atualizar_fundamentos",
            lambda d: chamadas.append(("fundamentos", d)),
        )
        monkeypatch.setattr(
            cli_acoes,
            "atualizar_documentos",
            lambda d, t: chamadas.append(("documentos", d)),
        )
        monkeypatch.setattr(
            cli_acoes, "atualizar_noticias", lambda d: chamadas.append(("noticias", d))
        )
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(
            comp,
            "resolver_data_referencia",
            lambda: pytest.fail("a data de referência não deve ser consultada"),
        )
        cli_acoes._despachar_atualizar(
            argparse.Namespace(recurso="fundamentos", data=None)
        )
        cli_acoes._despachar_atualizar(
            argparse.Namespace(recurso="documentos", data=None, ticker="PETR4")
        )
        cli_acoes._despachar_atualizar(argparse.Namespace(recurso="noticias", data=None))
        assert [data for _, data in chamadas] == [date.today()] * 3

    def test_data_explicita_e_repassada(self, monkeypatch):
        chamadas = []
        monkeypatch.setattr(
            cli_acoes,
            "atualizar_fundamentos",
            lambda d: chamadas.append(("fundamentos", d)),
        )
        monkeypatch.setattr(
            cli_acoes,
            "atualizar_documentos",
            lambda d, t: chamadas.append(("documentos", d)),
        )
        monkeypatch.setattr(
            cli_acoes, "atualizar_noticias", lambda d: chamadas.append(("noticias", d))
        )
        explicita = date(2026, 10, 14)
        cli_acoes._despachar_atualizar(
            argparse.Namespace(recurso="fundamentos", data=explicita)
        )
        cli_acoes._despachar_atualizar(
            argparse.Namespace(recurso="documentos", data=explicita, ticker="PETR4")
        )
        cli_acoes._despachar_atualizar(
            argparse.Namespace(recurso="noticias", data=explicita)
        )
        assert [data for _, data in chamadas] == [explicita] * 3


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

    def test_lote_com_falha_encerra_com_codigo_1(self, capsys, monkeypatch):
        class _LockNulo:
            def adquirir(self, esperar=0.0):
                return self

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

        monkeypatch.setattr(cli_acoes, "ActionLock", _LockNulo)
        monkeypatch.setattr(
            cli_acoes,
            "_despachar_acao",
            lambda args: {
                "resultados": {
                    "PETR4": {"erro": {"motivo": "falha_resumo", "detalhe": "x"}}
                },
                "falha": True,
            },
        )
        with pytest.raises(SystemExit) as exc:
            cli_acoes.executar_acao(
                self._args(comando="resumir", recurso="documentos", ticker=None)
            )
        assert exc.value.code == 1
        saida = json.loads(capsys.readouterr().out)
        assert saida["falha"] is True


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


class _ResultadoResumos:
    def __init__(self, sem_texto=0, nao_conclusivos=None, apontadores=None):
        self.sem_texto = sem_texto
        self.nao_conclusivos = nao_conclusivos or []
        self.apontadores = apontadores or []


class _DocumentosLlm(_DocumentosFake):
    def __init__(self, disponivel=True):
        super().__init__(disponivel=disponivel)
        self.chamadas = 0

    def llm_available(self):
        self.chamadas += 1
        return self._disponivel


class TestParserResumirDocumentos:
    def _parser(self):
        from flowscope.presentation.cli import build_parser

        return build_parser()

    def test_sem_ticker(self):
        args = self._parser().parse_args(["resumir", "documentos"])
        assert args.ticker is None

    def test_com_ticker(self):
        args = self._parser().parse_args(["resumir", "documentos", "petr4"])
        assert args.ticker == "petr4"

    def test_despacho_repassa_none(self, monkeypatch):
        repassados = []
        monkeypatch.setattr(
            cli_acoes, "resumir_documentos", lambda t: repassados.append(t) or {}
        )
        cli_acoes._despachar_resumir(
            argparse.Namespace(recurso="documentos", ticker=None)
        )
        assert repassados == [None]


class TestProcessarTicker:
    def test_sucesso_usa_contagens(self, monkeypatch):
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=True))
        monkeypatch.setattr(cli_resumos, "_pendentes_documentos", lambda n, t: [object()])
        monkeypatch.setattr(
            cli_resumos,
            "executar_resumos",
            lambda ctx, painel, pend: _ResultadoResumos(
                sem_texto=1, nao_conclusivos=[object()], apontadores=[object()]
            ),
        )
        desfecho, falhou = cli_resumos._processar_ticker(nucleo, object(), "PETR4")
        assert desfecho == {
            "pendentes": 1,
            "sem_texto": 1,
            "nao_conclusivos": 1,
            "apontadores": 1,
        }
        assert falhou is False

    def test_excecao_vira_falha_resumo(self, monkeypatch):
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=True))

        def pendentes(n, t):
            raise RuntimeError("boom")

        monkeypatch.setattr(cli_resumos, "_pendentes_documentos", pendentes)
        desfecho, falhou = cli_resumos._processar_ticker(nucleo, object(), "PETR4")
        assert desfecho == {
            "erro": {"motivo": "falha_resumo", "detalhe": "boom"}
        }
        assert falhou is True

    def test_erro_do_contexto_vira_falha_resumo(self, monkeypatch):
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=True))
        monkeypatch.setattr(cli_resumos, "_pendentes_documentos", lambda n, t: [object()])

        def executar(ctx, painel, pend):
            ctx.erro(RuntimeError("item quebrado"))
            return _ResultadoResumos()

        monkeypatch.setattr(cli_resumos, "executar_resumos", executar)
        desfecho, falhou = cli_resumos._processar_ticker(nucleo, object(), "PETR4")
        assert desfecho["erro"]["motivo"] == "falha_resumo"
        assert desfecho["erro"]["detalhe"] == "item quebrado"
        assert falhou is True


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
        assert set(resultado) == {
            "pendentes",
            "sem_texto",
            "nao_conclusivos",
            "apontadores",
        }
        assert "resultados" not in resultado

    def test_lote_completo_usa_nucleo_e_llm_uma_vez(self, monkeypatch):
        monkeypatch.setattr(
            cli_resumos, "last_tickers", lambda: ["petr4", "VALE3", "PETR4"]
        )
        documentos = _DocumentosLlm()
        nucleo = argparse.Namespace(documentos=documentos)
        import flowscope.presentation.composicao as comp

        montagens = []
        monkeypatch.setattr(
            comp, "montar_nucleo", lambda: montagens.append(1) or nucleo
        )
        processados = []

        def processar(n, painel, ticker):
            processados.append(ticker)
            return ({"pendentes": 1, "sem_texto": 0, "nao_conclusivos": 0,
                     "apontadores": 0}, False)

        monkeypatch.setattr(cli_resumos, "_processar_ticker", processar)
        resultado = cli_acoes.resumir_documentos(None)
        assert list(resultado["resultados"]) == ["PETR4", "VALE3"]
        assert resultado["falha"] is False
        assert processados == ["PETR4", "VALE3"]
        assert len(montagens) == 1
        assert documentos.chamadas == 1

    def test_lote_com_falha_parcial_nao_aborta(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: ["PETR4", "VALE3"])
        nucleo = argparse.Namespace(documentos=_DocumentosLlm())
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        processados = []

        def processar(n, painel, ticker):
            processados.append(ticker)
            if ticker == "PETR4":
                return ({"erro": {"motivo": "falha_resumo", "detalhe": "x"}}, True)
            return ({"pendentes": 0, "sem_texto": 0, "nao_conclusivos": 0,
                     "apontadores": 0}, False)

        monkeypatch.setattr(cli_resumos, "_processar_ticker", processar)
        resultado = cli_acoes.resumir_documentos(None)
        assert processados == ["PETR4", "VALE3"]
        assert resultado["resultados"]["PETR4"]["erro"]["motivo"] == "falha_resumo"
        assert resultado["falha"] is True

    def test_lote_sem_watchlist(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: [])
        import flowscope.presentation.composicao as comp

        montagens = []
        monkeypatch.setattr(comp, "montar_nucleo", lambda: montagens.append(1))
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_documentos(None)
        assert exc.value.motivo == "watchlist_ausente"
        assert not montagens

    def test_lote_sem_llm(self, monkeypatch):
        monkeypatch.setattr(cli_resumos, "last_tickers", lambda: ["PETR4"])
        nucleo = argparse.Namespace(documentos=_DocumentosFake(disponivel=False))
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        processados = []
        monkeypatch.setattr(
            cli_resumos,
            "_processar_ticker",
            lambda n, p, t: processados.append(t) or ({}, False),
        )
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_documentos(None)
        assert exc.value.motivo == "llm_nao_configurada"
        assert not processados

    def test_resumir_noticias_sem_llm(self, monkeypatch):
        nucleo = argparse.Namespace(noticias=_NoticiasFake(disponivel=False))
        import flowscope.presentation.composicao as comp

        monkeypatch.setattr(comp, "montar_nucleo", lambda: nucleo)
        with pytest.raises(cli_acoes.AcaoError) as exc:
            cli_acoes.resumir_noticias()
        assert exc.value.motivo == "llm_nao_configurada"
