"""Testes dos subcomandos ``flowscope nav`` da CLI."""

import argparse
import json

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

    def test_mcp_flag(self) -> None:
        args = cli.build_parser().parse_args(["--mcp"])
        assert args.mcp is True
        assert args.comando is None

    def test_sem_subcomando_mantem_comportamento(self) -> None:
        args = cli.build_parser().parse_args(["--vwap"])
        assert args.vwap is True
        assert args.comando is None


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
            "flowscope.presentation.cli.iniciar_mcp", lambda: chamadas.append(True)
        )
        monkeypatch.setattr("sys.argv", ["flowscope", "--mcp"])
        main.main()
        assert chamadas == [True]

    def test_mcp_nao_colide_com_flags(self, monkeypatch) -> None:
        from flowscope.presentation import main

        chamadas: list = []
        monkeypatch.setattr(main, "build_parser", lambda: cli.build_parser())
        monkeypatch.setattr(main, "_export", lambda *a: chamadas.append("vwap"))
        monkeypatch.setattr("sys.argv", ["flowscope", "--vwap"])
        main.main()
        assert chamadas == ["vwap"]
