"""Testes dos subcomandos ``flowscope nav`` da CLI."""

import argparse
import json
from datetime import date

import pytest

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_folha,
    no_interno,
    ramo_fundamentos,
)
from flowscope.application.navegacao.core import NavegacaoCore
from flowscope.presentation import cli


def _core() -> NavegacaoCore:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            valores={"PETR4": "[PETR4] PL=3.2", "VALE3": "[VALE3] PL=5.0"},
        )
    )
    raiz.filho(
        no_folha(
            "/doc/texto",
            "texto",
            carregar=lambda: "conteudo pesado",
            campo_pesado="texto",
        )
    )
    return NavegacaoCore(ArvoreConhecimento(raiz, assinatura="sig"))


def _args(**kwargs) -> argparse.Namespace:
    base = {"pretty": False}
    base.update(kwargs)
    return argparse.Namespace(**base)


class TestParser:
    def test_listar(self) -> None:
        args = cli.build_parser().parse_args(["nav", "listar", "/noticias/grupos"])
        assert args.comando == "nav"
        assert args.operacao == "listar"
        assert args.caminho == "/noticias/grupos"

    def test_obter_flags(self) -> None:
        args = cli.build_parser().parse_args(
            ["nav", "obter", "/x", "--offset", "0", "--limite", "12000"]
        )
        assert args.offset == 0
        assert args.limite == 12000

    def test_buscar_flags(self) -> None:
        args = cli.build_parser().parse_args(
            ["nav", "buscar", "/x", "--regex", "a", "--em", "titulo,texto", "--max", "50"]
        )
        assert args.regex == "a"
        assert args.em == "titulo,texto"
        assert args.max == 50

    def test_buscar_semantico_flags(self) -> None:
        args = cli.build_parser().parse_args(
            ["nav", "buscar-semantico", "/x", "--consulta", "q", "--max", "10"]
        )
        assert args.operacao == "buscar-semantico"
        assert args.consulta == "q"

    def test_cursor_na_listagem(self) -> None:
        args = cli.build_parser().parse_args(
            ["nav", "listar", "/x", "--cursor", "TOKEN"]
        )
        assert args.cursor == "TOKEN"

    def test_manifesto_sem_caminho(self) -> None:
        args = cli.build_parser().parse_args(["nav", "manifesto"])
        assert args.operacao == "manifesto"

    def test_alias_mcp_removido(self) -> None:
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(["--mcp"])

    def test_flags_planas_removidas(self) -> None:
        with pytest.raises(SystemExit):
            cli.build_parser().parse_args(["--vwap"])


class TestCamposNav:
    def test_em_vira_lista(self) -> None:
        campos = cli._campos_nav(_args(caminho="/x", regex="a", em="titulo, texto"))
        assert campos["em"] == ["titulo", "texto"]

    def test_operacao_mapping(self) -> None:
        assert cli._operacao_nav("buscar-semantico") == "buscar_semantico"
        assert cli._operacao_nav("listar") == "listar"


class TestExecutarNav:
    def test_listar_imprime_json(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli, "montar_core_navegacao", _core)
        cli.executar_nav(_args(operacao="listar", caminho="/fundamentos"))
        payload = json.loads(capsys.readouterr().out)
        assert [item["nome"] for item in payload["itens"]] == [
            "data-referencia",
            "tickers",
            "valores",
        ]

    def test_pretty_indenta(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli, "montar_core_navegacao", _core)
        cli.executar_nav(_args(operacao="listar", caminho="/fundamentos", pretty=True))
        assert "\n  " in capsys.readouterr().out

    def test_erro_imprime_json_e_diagnostico(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli, "montar_core_navegacao", _core)
        with pytest.raises(SystemExit) as saida:
            cli.executar_nav(_args(operacao="obter", caminho="/nao/existe"))
        assert saida.value.code == 1
        capturado = capsys.readouterr()
        payload = json.loads(capturado.out)
        assert payload["motivo"] == "caminho_invalido"
        assert "caminho_invalido" in capturado.err

    def test_manifesto(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli, "montar_core_navegacao", _core)
        cli.executar_nav(_args(operacao="manifesto"))
        payload = json.loads(capsys.readouterr().out)
        assert "listar" in payload["result"]


class TestDispatchMain:
    def test_main_despacha_nav(self, monkeypatch) -> None:
        from flowscope.presentation import main

        chamadas: list = []
        monkeypatch.setattr(main, "build_parser", lambda: cli.build_parser())
        monkeypatch.setattr(
            "flowscope.presentation.cli.executar_nav", lambda args: chamadas.append(args)
        )
        monkeypatch.setattr("sys.argv", ["flowscope", "nav", "listar", "/x"])
        main.main()
        assert chamadas and chamadas[0].operacao == "listar"

    def test_main_despacha_mcp(self, monkeypatch) -> None:
        from flowscope.presentation import main

        chamadas: list = []
        monkeypatch.setattr(main, "build_parser", lambda: cli.build_parser())
        monkeypatch.setattr(
            "flowscope.presentation.cli.iniciar_mcp", lambda *a: chamadas.append(True)
        )
        monkeypatch.setattr("sys.argv", ["flowscope", "mcp"])
        main.main()
        assert chamadas == [True]

    def test_main_despacha_exportar(self, monkeypatch) -> None:
        from flowscope.presentation import main

        chamadas: list = []
        monkeypatch.setattr(main, "build_parser", lambda: cli.build_parser())
        monkeypatch.setattr(
            "flowscope.presentation.cli_consultas.executar_exportar",
            lambda args: chamadas.append(args.recurso),
        )
        monkeypatch.setattr("sys.argv", ["flowscope", "exportar", "vwap"])
        main.main()
        assert chamadas == ["vwap"]


class TestDataReferenciaCli:
    def _core_com_data(self):
        from datetime import date

        raiz = no_interno("/", "raiz")
        raiz.filho(
            ramo_fundamentos(
                tickers=["PETR4"],
                valores={"PETR4": "[PETR4] PL=3.2"},
                data_referencia=date(2026, 10, 14),
            )
        )
        return NavegacaoCore(ArvoreConhecimento(raiz))

    def test_parser_aceita_data_referencia(self) -> None:
        args = cli.build_parser().parse_args(["nav", "data-referencia"])
        assert args.comando == "nav"
        assert args.operacao == "data-referencia"

    def test_operacao_mapping(self) -> None:
        assert cli._operacao_nav("data-referencia") == "data_referencia"

    def test_executa_imprime_json(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli, "montar_core_navegacao", self._core_com_data)
        cli.executar_nav(_args(operacao="data-referencia"))
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"data": "2026-10-14"}


class TestCargaDataAware:
    def test_carregar_fundamentos_usa_data_de_referencia(self, monkeypatch) -> None:
        from datetime import date

        import flowscope.infrastructure.fii.fundamental_history_store as mod

        registros = {
            ("PETR4", date(2026, 1, 1)): "antiga",
            ("PETR4", date(2026, 2, 1)): "nova",
        }

        class FakeStore:
            def obter_em_ou_antes(self, ticker, data):
                anteriores = [
                    d for (t, d) in registros if t == ticker and d <= data
                ]
                return registros.get((ticker, max(anteriores))) if anteriores else None

            def datas(self, ticker):
                return sorted(d for (t, d) in registros if t == ticker)

            def obter(self, ticker, data):
                return registros.get((ticker, data))

        monkeypatch.setattr(mod, "JsonFundamentalHistoryStore", FakeStore)
        assert cli._carregar_fundamentos(["PETR4"], date(2026, 1, 15)) == {
            "PETR4": "antiga"
        }
        assert cli._carregar_fundamentos(["PETR4"], None) == {"PETR4": "nova"}

    def test_composicao_reflete_data_pedida(self, monkeypatch) -> None:
        from datetime import date

        core = cli.montar_core_navegacao(reference_date=date(2020, 1, 2))
        assert core.executar("data_referencia", {}).dados == {"data": "2020-01-02"}


class TestSubcomandoMcp:
    def test_parser_mcp_com_params(self) -> None:
        parser = cli.build_parser()
        args = parser.parse_args(
            ["mcp", "--watchlist", "carteira.txt", "--data", "2026-10-14"]
        )
        assert args.comando == "mcp"
        assert args.watchlist == "carteira.txt"
        assert args.data == date(2026, 10, 14)

    def test_alias_mcp_rejeitado(self) -> None:
        parser = cli.build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--mcp"])

    def test_sem_params_nao_prepara(self, monkeypatch) -> None:
        chamadas: list = []
        monkeypatch.setattr(
            "flowscope.presentation.navegacao.executar_servidor",
            lambda core: chamadas.append(core),
        )
        monkeypatch.setattr(cli, "montar_core_navegacao", lambda reference_date=None: "tree")
        cli.iniciar_mcp()
        assert chamadas == ["tree"]

    def test_preparacao_reusa_nucleos_e_serve(self, monkeypatch, capsys) -> None:
        from flowscope.presentation import cli_acoes

        eventos: list = []
        monkeypatch.setattr(
            cli_acoes, "carregar_watchlist", lambda arq: eventos.append(("wl", arq))
        )
        monkeypatch.setattr(
            cli_acoes, "atualizar_fundamentos", lambda d: eventos.append(("fund", d))
        )
        monkeypatch.setattr(
            "flowscope.presentation.navegacao.executar_servidor",
            lambda core: eventos.append(("serve", core)),
        )
        monkeypatch.setattr(cli, "montar_core_navegacao", lambda reference_date=None: "tree")
        cli.iniciar_mcp("carteira.txt", date(2026, 10, 14))
        assert eventos == [
            ("wl", "carteira.txt"),
            ("fund", date(2026, 10, 14)),
            ("serve", "tree"),
        ]
        assert capsys.readouterr().out == ""

    def test_falha_na_preparacao_aborta_sem_servir(self, monkeypatch) -> None:
        from flowscope.presentation import cli_acoes

        def falha(arquivo):
            raise cli_acoes.AcaoError("arquivo_inexistente", arquivo)

        serviu: list = []
        monkeypatch.setattr(cli_acoes, "carregar_watchlist", falha)
        monkeypatch.setattr(
            "flowscope.presentation.navegacao.executar_servidor",
            lambda core: serviu.append(core),
        )
        with pytest.raises(SystemExit) as exc:
            cli.iniciar_mcp("nao.txt", None)
        assert exc.value.code == 1
        assert serviu == []
