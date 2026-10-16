"""Servidor MCP embutido e catálogo de tools ``nav_*`` do FlowScope.

Implementa um servidor JSON-RPC 2.0 próprio sobre stdio (sem dependência nova),
alvo da revisão moderna ``2026-07-28`` do MCP: cada requisição declara a versão
em ``_meta`` e a RPC obrigatória ``server/discover`` devolve as versões
suportadas, as capacidades e a identidade. As operações de navegação são
expostas como tools independentes ``nav_*`` (ordem alfabética determinística),
todas reusando o :class:`NavegacaoCore`. O ``stdout`` só recebe JSON-RPC válido;
logs e diagnósticos vão para ``stderr``.

Este módulo é estritamente de apresentação: recebe o núcleo pronto do ponto de
composição (``cli.py``/``main.py``) e não importa infraestrutura.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from typing import TextIO

from flowscope import __version__
from flowscope.application.navegacao.core import NavegacaoCore

logger = logging.getLogger("flowscope")

#: Revisão do MCP implementada por esta mudança.
REVISAO_PROTOCOLO = "2026-07-28"

#: Versões de protocolo suportadas.
REVISOES_SUPORTADAS = (REVISAO_PROTOCOLO,)

#: Identidade do servidor anunciada em ``server/discover``.
IDENTIDADE = {"name": "flowscope", "version": __version__}

#: Anotações comuns das tools de navegação (todas somente-leitura).
ANOTACOES = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}

#: Códigos de erro JSON-RPC usados pelo servidor.
ERRO_PARSE = -32700
ERRO_REQUISICAO = -32600
ERRO_METODO = -32601
ERRO_PARAMS = -32602
ERRO_INTERNO = -32603


@dataclass(frozen=True)
class Tool:
    """Especificação de uma tool MCP de navegação."""

    nome: str
    operacao: str
    titulo: str
    descricao: str
    schema: dict


_CAMINHO = {"type": "string", "description": "Caminho canônico do nó."}
_CURSOR = {"type": "string", "description": "Cursor opaco de continuação."}

#: Catálogo das tools ``nav_*`` em ordem alfabética determinística.
CATALOGO: tuple[Tool, ...] = (
    Tool(
        nome="nav_buscar",
        operacao="buscar",
        titulo="Buscar por regex",
        descricao="Busca determinística por expressão regular nos campos dos nós.",
        schema={
            "type": "object",
            "properties": {
                "caminho": _CAMINHO,
                "regex": {"type": "string", "description": "Expressão regular."},
                "em": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos pesquisáveis.",
                },
                "max": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 50,
                },
                "cursor": _CURSOR,
            },
            "required": ["caminho", "regex"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="nav_buscar_semantico",
        operacao="buscar_semantico",
        titulo="Buscar semanticamente",
        descricao="Busca por similaridade semântica, com fallback quando não há índice.",
        schema={
            "type": "object",
            "properties": {
                "caminho": _CAMINHO,
                "consulta": {"type": "string", "description": "Texto da consulta."},
                "max": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 10,
                },
                "cursor": _CURSOR,
            },
            "required": ["caminho", "consulta"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="nav_contar",
        operacao="contar",
        titulo="Contar nós",
        descricao="Conta os nós da subárvore prefixada pelo caminho.",
        schema={
            "type": "object",
            "properties": {"caminho": _CAMINHO},
            "required": ["caminho"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="nav_data_referencia",
        operacao="data_referencia",
        titulo="Data de referência",
        descricao=(
            "Devolve a data de referência resolvida da última carga de fundamentos."
        ),
        schema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    Tool(
        nome="nav_existe",
        operacao="existe",
        titulo="Verificar existência",
        descricao="Indica se o caminho existe na árvore.",
        schema={
            "type": "object",
            "properties": {"caminho": _CAMINHO},
            "required": ["caminho"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="nav_listar",
        operacao="listar",
        titulo="Listar filhos",
        descricao="Lista os filhos imediatos de um nó interno, com paginação.",
        schema={
            "type": "object",
            "properties": {"caminho": _CAMINHO, "cursor": _CURSOR},
            "required": ["caminho"],
            "additionalProperties": False,
        },
    ),
    Tool(
        nome="nav_manifesto",
        operacao="manifesto",
        titulo="Obter manifesto",
        descricao="Devolve o manifesto de navegação determinístico da árvore.",
        schema={"type": "object", "properties": {}, "additionalProperties": False},
    ),
    Tool(
        nome="nav_obter",
        operacao="obter",
        titulo="Obter conteúdo",
        descricao="Devolve o conteúdo de um nó folha, paginando o conteúdo pesado.",
        schema={
            "type": "object",
            "properties": {
                "caminho": _CAMINHO,
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limite": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 12000,
                    "default": 12000,
                },
            },
            "required": ["caminho"],
            "additionalProperties": False,
        },
    ),
)

#: Índice das tools por nome.
CATALOGO_POR_NOME = {tool.nome: tool for tool in CATALOGO}


class ErroTool(Exception):
    """Erro ao processar uma chamada de tool (tool desconhecida)."""


def validar_schema(schema: dict, argumentos: object) -> str | None:
    """Valida os argumentos contra o schema, devolvendo o erro ou ``None``."""
    if not isinstance(argumentos, dict):
        return "os argumentos devem ser um objeto"
    propriedades = schema.get("properties", {})
    for nome in schema.get("required", ()):
        if nome not in argumentos:
            return f"campo obrigatório ausente: {nome}"
    for nome, valor in argumentos.items():
        if nome not in propriedades:
            return f"campo desconhecido: {nome}"
        erro = _validar_valor(propriedades[nome], valor, nome)
        if erro:
            return erro
    return None


def _validar_valor(spec: dict, valor: object, nome: str) -> str | None:
    """Valida um valor individual conforme o tipo e as faixas do schema."""
    tipo = spec.get("type")
    if tipo == "array":
        return _validar_array(spec, valor, nome)
    erro = _validar_escalar(tipo, valor, nome)
    if erro:
        return erro
    return _validar_faixa(spec, valor, nome)


def _validar_escalar(tipo: object, valor: object, nome: str) -> str | None:
    """Valida o tipo de um valor escalar (texto, inteiro ou booleano)."""
    if tipo == "string" and not isinstance(valor, str):
        return f"o campo '{nome}' deve ser texto"
    if tipo == "integer" and (isinstance(valor, bool) or not isinstance(valor, int)):
        return f"o campo '{nome}' deve ser um inteiro"
    if tipo == "boolean" and not isinstance(valor, bool):
        return f"o campo '{nome}' deve ser booleano"
    return None


def _validar_array(spec: dict, valor: object, nome: str) -> str | None:
    """Valida uma lista e os seus elementos contra o schema do item."""
    if not isinstance(valor, list):
        return f"o campo '{nome}' deve ser uma lista"
    item = spec.get("items")
    for elemento in valor:
        if item is not None and (erro := _validar_valor(item, elemento, nome)):
            return erro
    return None


def _validar_faixa(spec: dict, valor: object, nome: str) -> str | None:
    """Valida os limites ``minimum``/``maximum`` de um valor numérico."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None
    minimo = spec.get("minimum")
    maximo = spec.get("maximum")
    if minimo is not None and valor < minimo:
        return f"o campo '{nome}' deve ser no mínimo {minimo}"
    if maximo is not None and valor > maximo:
        return f"o campo '{nome}' deve ser no máximo {maximo}"
    return None


def _erro_jsonrpc(id_: object, codigo: int, mensagem: str, dados: object = None) -> dict:
    """Monta uma resposta de erro JSON-RPC."""
    erro: dict = {"code": codigo, "message": mensagem}
    if dados is not None:
        erro["data"] = dados
    return {"jsonrpc": "2.0", "id": id_, "error": erro}


def _sucesso(id_: object, resultado: object) -> dict:
    """Monta uma resposta JSON-RPC de sucesso."""
    return {"jsonrpc": "2.0", "id": id_, "result": resultado}


class ServidorMCP:
    """Servidor MCP stdio em JSON-RPC newline-delimited."""

    def __init__(
        self: ServidorMCP,
        core: NavegacaoCore,
        entrada: TextIO | None = None,
        saida: TextIO | None = None,
    ) -> None:
        """Guarda o núcleo de navegação e os canais de entrada e saída."""
        self._core = core
        self._entrada = entrada if entrada is not None else sys.stdin
        self._saida = saida if saida is not None else sys.stdout

    def servir(self: ServidorMCP) -> None:
        """Lê requisições até o EOF e encerra sem erro."""
        for linha in self._entrada:
            texto = linha.strip()
            if not texto:
                continue
            try:
                requisicao = json.loads(texto)
            except json.JSONDecodeError:
                self._escrever(_erro_jsonrpc(None, ERRO_PARSE, "Parse error"))
                continue
            resposta = self._tratar(requisicao)
            if resposta is not None:
                self._escrever(resposta)

    def _escrever(self: ServidorMCP, mensagem: dict) -> None:
        """Escreve uma mensagem JSON-RPC, delimitada por newline, no stdout."""
        self._saida.write(json.dumps(mensagem, ensure_ascii=False) + "\n")
        self._saida.flush()

    def _tratar(self: ServidorMCP, requisicao: object) -> dict | None:
        """Trata uma mensagem JSON-RPC e devolve a resposta, ou ``None``."""
        if not isinstance(requisicao, dict) or "method" not in requisicao:
            return _erro_jsonrpc(_id(requisicao), ERRO_REQUISICAO, "Invalid Request")
        metodo = requisicao.get("method")
        params = requisicao.get("params") or {}
        if "id" not in requisicao:
            self._tratar_notificacao(metodo)
            return None
        id_ = requisicao.get("id")
        erro_versao = self._checar_versao(params)
        if erro_versao is not None:
            erro_versao["id"] = id_
            return erro_versao
        return self._despachar(id_, metodo, params)

    def _despachar(self: ServidorMCP, id_: object, metodo: object, params: dict) -> dict:
        """Executa o método JSON-RPC solicitado."""
        if metodo == "server/discover":
            return _sucesso(id_, self._descobrir())
        if metodo == "ping":
            return _sucesso(id_, {})
        if metodo == "tools/list":
            return _sucesso(id_, {"tools": [self._tool_dict(t) for t in CATALOGO]})
        if metodo == "tools/call":
            return self._tools_call(id_, params)
        if metodo == "initialize":
            return _erro_jsonrpc(
                id_,
                ERRO_METODO,
                "initialize não é suportado; versões suportadas: "
                + ", ".join(REVISOES_SUPORTADAS),
                {"error": "UnsupportedProtocolVersionError",
                 "supported": list(REVISOES_SUPORTADAS)},
            )
        return _erro_jsonrpc(id_, ERRO_METODO, f"Método não encontrado: {metodo}")

    def _checar_versao(self: ServidorMCP, params: object) -> dict | None:
        """Recusa a requisição quando a versão declarada em ``_meta`` é inválida."""
        if not isinstance(params, dict):
            return None
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            return None
        versao = meta.get("protocolVersion")
        if versao is None or versao in REVISOES_SUPORTADAS:
            return None
        return _erro_jsonrpc(
            None,
            ERRO_PARAMS,
            "UnsupportedProtocolVersionError",
            {
                "error": "UnsupportedProtocolVersionError",
                "supported": list(REVISOES_SUPORTADAS),
                "requested": versao,
            },
        )

    def _tratar_notificacao(self: ServidorMCP, metodo: object) -> None:
        """Trata notificações; o cancelamento é registrado sem resposta."""
        if metodo == "notifications/cancelled":
            logger.info("Requisição MCP cancelada pelo cliente")
        else:
            logger.debug("Notificação MCP ignorada: %s", metodo)

    def _descobrir(self: ServidorMCP) -> dict:
        """Monta o resultado de ``server/discover``."""
        return {
            "protocolVersions": list(REVISOES_SUPORTADAS),
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": dict(IDENTIDADE),
        }

    @staticmethod
    def _tool_dict(tool: Tool) -> dict:
        """Serializa uma tool para ``tools/list``."""
        return {
            "name": tool.nome,
            "title": tool.titulo,
            "description": tool.descricao,
            "inputSchema": tool.schema,
            "annotations": dict(ANOTACOES),
        }

    def _tools_call(self: ServidorMCP, id_: object, params: object) -> dict:
        """Valida e executa uma tool, devolvendo o envelope de resultado."""
        if not isinstance(params, dict):
            return _erro_jsonrpc(id_, ERRO_PARAMS, "parâmetros inválidos")
        nome = params.get("name")
        tool = CATALOGO_POR_NOME.get(nome)
        if tool is None:
            return _erro_jsonrpc(id_, ERRO_PARAMS, f"tool não encontrada: {nome}")
        argumentos = params.get("arguments") or {}
        erro_schema = validar_schema(tool.schema, argumentos)
        if erro_schema:
            estruturado = {
                "erro": {
                    "motivo": "schema_invalido",
                    "detalhe": erro_schema,
                    "dica": "revise os argumentos conforme o inputSchema da tool",
                }
            }
            return _sucesso(id_, self._envelope(estruturado, is_error=False))
        try:
            resultado = self._core.executar(tool.operacao, argumentos)
        except ErroTool as exc:
            return _erro_jsonrpc(id_, ERRO_PARAMS, str(exc))
        if resultado.erro is not None:
            return _sucesso(
                id_,
                self._envelope(
                    {"erro": resultado.erro}, is_error=resultado.falha_interna
                ),
            )
        return _sucesso(id_, self._envelope(conteudo(resultado.dados), is_error=False))

    @staticmethod
    def _envelope(conteudo: object, is_error: bool) -> dict:
        """Monta o envelope MCP de uma chamada de tool."""
        resultado = {
            "content": [
                {"type": "text", "text": json.dumps(conteudo, ensure_ascii=False)}
            ],
            "structuredContent": conteudo,
        }
        if is_error:
            resultado["isError"] = True
        return resultado


def _id(requisicao: object) -> object:
    """Extrai o ``id`` de uma requisição, quando houver."""
    return requisicao.get("id") if isinstance(requisicao, dict) else None


def conteudo(dados: object) -> object:
    """Normaliza o conteúdo estruturado: dicionários diretos, demais em ``result``."""
    if isinstance(dados, dict):
        return dados
    return {"result": dados}


def executar_servidor(core: NavegacaoCore) -> None:
    """Inicia o servidor MCP stdio, roteando logs para ``stderr``."""
    logging.basicConfig(
        level=logging.INFO, stream=sys.stderr, force=True
    )
    ServidorMCP(core).servir()
