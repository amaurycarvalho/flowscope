"""Testes do servidor MCP stdio e do catálogo de tools ``nav_*``."""

import io
import json

import pytest

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_folha,
    no_interno,
    ramo_fundamentos,
)
from flowscope.application.navegacao.core import NavegacaoCore
from flowscope.presentation.navegacao import (
    CATALOGO,
    REVISAO_PROTOCOLO,
    ServidorMCP,
)


def _core() -> NavegacaoCore:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            campos={"PL": "preço/lucro"},
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


def _executar(core: NavegacaoCore, *requisicoes: dict) -> list[dict]:
    entrada = io.StringIO("\n".join(json.dumps(r) for r in requisicoes) + "\n")
    saida = io.StringIO()
    ServidorMCP(core, entrada=entrada, saida=saida).servir()
    return [json.loads(linha) for linha in saida.getvalue().splitlines() if linha]


def _requisicao(metodo: str, params: dict | None = None, id_: object = 1) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "method": metodo, "params": params or {}}


class TestCanalStdio:
    def test_encerra_em_eof(self) -> None:
        respostas = _executar(_core(), _requisicao("ping"))
        assert respostas[0]["result"] == {}

    def test_stdout_so_json_rpc(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao("server/discover"),
            _requisicao("tools/list"),
            _requisicao("ping"),
        )
        assert len(respostas) == 3
        for resposta in respostas:
            assert resposta["jsonrpc"] == "2.0"

    def test_parse_error_nao_encerra(self) -> None:
        entrada = io.StringIO("{nao-json}\n" + json.dumps(_requisicao("ping")) + "\n")
        saida = io.StringIO()
        ServidorMCP(_core(), entrada=entrada, saida=saida).servir()
        linhas = [json.loads(linha) for linha in saida.getvalue().splitlines()]
        assert linhas[0]["error"]["code"] == -32700
        assert linhas[1]["result"] == {}


class TestDiscover:
    def test_versao_suportada(self) -> None:
        respostas = _executar(_core(), _requisicao("server/discover"))
        resultado = respostas[0]["result"]
        assert REVISAO_PROTOCOLO in resultado["protocolVersions"]
        assert "tools" in resultado["capabilities"]
        assert resultado["serverInfo"]["name"] == "flowscope"

    def test_negociacao_por_meta(self) -> None:
        requisicao = _requisicao(
            "server/discover", {"_meta": {"protocolVersion": REVISAO_PROTOCOLO}}
        )
        respostas = _executar(_core(), requisicao)
        assert "result" in respostas[0]

    def test_versao_nao_suportada(self) -> None:
        requisicao = _requisicao(
            "server/discover", {"_meta": {"protocolVersion": "1900-01-01"}}
        )
        respostas = _executar(_core(), requisicao)
        erro = respostas[0]["error"]
        assert erro["message"] == "UnsupportedProtocolVersionError"
        assert REVISAO_PROTOCOLO in erro["data"]["supported"]

    def test_initialize_legado_recebe_erro(self) -> None:
        respostas = _executar(_core(), _requisicao("initialize", {"protocolVersion": "x"}))
        erro = respostas[0]["error"]
        assert REVISAO_PROTOCOLO in erro["message"]


class TestToolsList:
    def test_oito_tools_em_ordem_alfabetica(self) -> None:
        respostas = _executar(_core(), _requisicao("tools/list"))
        nomes = [tool["name"] for tool in respostas[0]["result"]["tools"]]
        assert nomes == sorted(nomes)
        assert nomes == [tool.nome for tool in CATALOGO]
        assert len(nomes) == 8

    def test_annotations_e_title(self) -> None:
        respostas = _executar(_core(), _requisicao("tools/list"))
        for tool in respostas[0]["result"]["tools"]:
            assert tool["title"]
            assert tool["annotations"] == {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": False,
            }
            assert "inputSchema" in tool


class TestToolsCall:
    def test_data_referencia_disponivel(self) -> None:
        from datetime import date

        raiz = no_interno("/", "raiz")
        raiz.filho(
            ramo_fundamentos(
                tickers=["PETR4"],
                valores={"PETR4": "[PETR4] PL=3.2"},
                data_referencia=date(2026, 10, 14),
            )
        )
        core = NavegacaoCore(ArvoreConhecimento(raiz))
        respostas = _executar(
            core,
            _requisicao(
                "tools/call",
                {"name": "nav_data_referencia", "arguments": {}},
            ),
        )
        resultado = respostas[0]["result"]
        assert resultado["structuredContent"] == {"data": "2026-10-14"}
        assert "isError" not in resultado

    def test_data_referencia_ausente_sem_erro(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {"name": "nav_data_referencia", "arguments": {}},
            ),
        )
        resultado = respostas[0]["result"]
        assert resultado["structuredContent"] == {"data": None}
        assert "isError" not in resultado

    def test_listar(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {"name": "nav_listar", "arguments": {"caminho": "/fundamentos"}},
            ),
        )
        conteudo = respostas[0]["result"]["structuredContent"]
        assert [item["nome"] for item in conteudo["itens"]] == [
            "campos",
            "data-referencia",
            "tickers",
            "valores",
        ]
        assert "isError" not in respostas[0]["result"]

    def test_existe(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {"name": "nav_existe", "arguments": {"caminho": "/fundamentos"}},
            ),
        )
        assert respostas[0]["result"]["structuredContent"] == {"result": True}

    def test_buscar_com_cursor(self) -> None:
        primeira = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {
                    "name": "nav_buscar",
                    "arguments": {"caminho": "/fundamentos", "regex": "PL", "max": 1},
                },
            ),
        )[0]["result"]["structuredContent"]
        assert "nextCursor" in primeira
        continuacao = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {
                    "name": "nav_buscar",
                    "arguments": {
                        "caminho": "/fundamentos",
                        "regex": "PL",
                        "max": 1,
                        "cursor": primeira["nextCursor"],
                    },
                },
            ),
        )[0]["result"]["structuredContent"]
        assert len(continuacao["resultados"]) == 1
        assert continuacao["resultados"] != primeira["resultados"]

    def test_schema_invalido(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {
                    "name": "nav_buscar",
                    "arguments": {"caminho": "/fundamentos", "regex": "PL", "max": 99},
                },
            ),
        )
        conteudo = respostas[0]["result"]["structuredContent"]
        assert conteudo["erro"]["motivo"] == "schema_invalido"
        assert "isError" not in respostas[0]["result"]

    def test_tool_desconhecida(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao("tools/call", {"name": "nav_inexistente", "arguments": {}}),
        )
        assert "error" in respostas[0]
        assert "não encontrada" in respostas[0]["error"]["message"]

    def test_erro_recuperavel_sem_iserror(self) -> None:
        respostas = _executar(
            _core(),
            _requisicao(
                "tools/call",
                {"name": "nav_obter", "arguments": {"caminho": "/nao/existe"}},
            ),
        )
        resultado = respostas[0]["result"]
        assert "isError" not in resultado
        assert resultado["structuredContent"]["erro"]["motivo"] == "caminho_invalido"

    def test_falha_interna_com_iserror(self, monkeypatch) -> None:
        core = _core()

        def explodir(_caminho):
            raise RuntimeError("boom")

        monkeypatch.setattr(core.arvore, "listar", explodir)
        respostas = _executar(
            core,
            _requisicao(
                "tools/call",
                {"name": "nav_listar", "arguments": {"caminho": "/fundamentos"}},
            ),
        )
        resultado = respostas[0]["result"]
        assert resultado["isError"] is True
        assert resultado["structuredContent"]["erro"]["motivo"] == "erro_interno"


class TestNotificacoes:
    def test_cancelamento_sem_resposta(self) -> None:
        notificacao = {
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": 1},
        }
        respostas = _executar(
            _core(), notificacao, _requisicao("ping", id_=2)
        )
        assert len(respostas) == 1
        assert respostas[0]["id"] == 2
