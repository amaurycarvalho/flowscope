"""Adaptador do protocolo JSON de navegação da árvore de conhecimento.

A LLM emite, a cada turno, um objeto ``{"resposta", "solicitacoes": [...]}``. O
parser é tolerante (bloco cercado, texto cru ou trecho entre chaves) e, sem JSON
reconhecido, todo o texto é tratado como resposta final. As operações canônicas
são validadas e executadas pelo :class:`NavegacaoCore`; este módulo apenas
serializa o bloco determinístico do chat (com ``foco``), trata o
``resetar_navegacao`` como preocupação do loop do chat e impõe o limite de 8
operações por turno.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flowscope.application.chat.arvore import ArvoreConhecimento

if TYPE_CHECKING:
    from flowscope.application.navegacao.core import NavegacaoCore, Resultado

logger = logging.getLogger("flowscope")

#: Operação de descarte do histórico, tratada pelo loop do chat (não no núcleo).
OPERACAO_RESET = "resetar_navegacao"

#: Máximo de operações por turno.
MAX_OPERACOES = 8

#: Marcador do bloco de resultado de navegação.
MARCADOR_RESULTADO = "[RESULTADO_NAVEGACAO]"

_MARCADOR_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class Solicitacao:
    """Operação pedida pela LLM, com os seus campos."""

    op: str
    campos: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RespostaProtocolo:
    """Resposta interpretada do turno."""

    resposta: str | None
    solicitacoes: list[Solicitacao] = field(default_factory=list)

    @property
    def final(self: RespostaProtocolo) -> bool:
        """Indica se a resposta é conclusiva (sem solicitações)."""
        return not self.solicitacoes


def extrair_json(texto: str) -> dict | None:
    """Extrai o objeto JSON da resposta, tentando formatos tolerantes."""
    if not texto:
        return None
    candidatos: list[str] = []
    cercado = _MARCADOR_JSON.search(texto)
    if cercado is not None:
        candidatos.append(cercado.group(1))
    candidatos.append(texto.strip())
    inicio, fim = texto.find("{"), texto.rfind("}")
    if 0 <= inicio < fim:
        candidatos.append(texto[inicio : fim + 1])
    for candidato in candidatos:
        try:
            dados = json.loads(candidato)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(dados, dict) and "resposta" in dados:
            return dados
    return None


def _texto_ou_nulo(valor: object) -> str | None:
    """Normaliza o campo ``resposta`` para texto sem espaços ou ``None``."""
    if isinstance(valor, str):
        return valor.strip() or None
    return None


def _solicitacoes(itens: object) -> list[Solicitacao]:
    """Normaliza a lista de solicitações, descartando itens inválidos."""
    if not isinstance(itens, list):
        return []
    return [
        Solicitacao(op=item["op"], campos={k: v for k, v in item.items() if k != "op"})
        for item in itens
        if isinstance(item, dict) and isinstance(item.get("op"), str)
    ]


def interpretar(texto: str) -> RespostaProtocolo:
    """Interpreta a resposta da LLM, tolerando formatos e texto puro."""
    dados = extrair_json(texto)
    if dados is None:
        return RespostaProtocolo(resposta=_texto_ou_nulo((texto or "").strip()))
    return RespostaProtocolo(
        resposta=_texto_ou_nulo(dados.get("resposta")),
        solicitacoes=_solicitacoes(dados.get("solicitacoes")),
    )


class ProtocoloNavegacao:
    """Adaptador fino sobre o núcleo: valida, executa e serializa o chat."""

    def __init__(
        self: ProtocoloNavegacao,
        arvore: ArvoreConhecimento,
        max_operacoes: int = MAX_OPERACOES,
        core: NavegacaoCore | None = None,
    ) -> None:
        """Guarda o núcleo, a árvore e o limite de operações por turno."""
        if core is None:
            from flowscope.application.navegacao.core import NavegacaoCore

            core = NavegacaoCore(arvore)
        self._arvore = arvore
        self._core = core
        self._max_operacoes = max_operacoes

    @property
    def core(self: ProtocoloNavegacao) -> NavegacaoCore:
        """Núcleo de navegação reusado pelo adaptador."""
        return self._core

    def validar(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> None:
        """Valida a operação, delegando ao núcleo (o reset é do chat)."""
        if solicitacao.op == OPERACAO_RESET:
            return
        self._core.validar(solicitacao.op, solicitacao.campos)

    def executar(
        self: ProtocoloNavegacao, solicitacoes: list[Solicitacao]
    ) -> list[dict]:
        """Executa as operações na ordem, agregando resultados estruturados."""
        if len(solicitacoes) > self._max_operacoes:
            excedente = solicitacoes[self._max_operacoes :]
            solicitacoes = solicitacoes[: self._max_operacoes]
            resultados = [self._executar_uma(s) for s in solicitacoes]
            resultados.append(
                {
                    "op": "limite_operacoes",
                    "erro": {
                        "motivo": "limite_operacoes",
                        "detalhe": f"{len(excedente)} excedentes",
                    },
                }
            )
            return resultados
        return [self._executar_uma(s) for s in solicitacoes]

    def _executar_uma(self: ProtocoloNavegacao, solicitacao: Solicitacao) -> dict:
        """Executa uma operação, capturando o erro estruturado."""
        base = {"op": solicitacao.op}
        caminho = solicitacao.campos.get("caminho")
        if caminho:
            base["caminho"] = caminho
        if solicitacao.op == OPERACAO_RESET:
            base["dados"] = "navegacao_descartada"
            return base
        resultado = self._core.executar(solicitacao.op, solicitacao.campos)
        self._preencher(base, resultado)
        return base

    @staticmethod
    def _preencher(base: dict, resultado: Resultado) -> None:
        """Preenche o bloco do chat com o resultado do núcleo."""
        if resultado.erro is not None:
            base["erro"] = resultado.erro
            return
        base["dados"] = _para_chat(resultado.dados)

    @staticmethod
    def serializar(resultados: list[dict], foco: str | None = None) -> str:
        """Serializa os resultados em um bloco determinístico.

        O ``foco`` é o último caminho obtido com sucesso e acompanha o bloco
        para o turno seguinte resolver referências anafóricas.
        """
        corpo: dict = {"resultados": resultados}
        if foco:
            corpo["foco"] = foco
        return f"{MARCADOR_RESULTADO} {json.dumps(corpo, ensure_ascii=False)}"

    def executar_e_serializar(
        self: ProtocoloNavegacao,
        solicitacoes: list[Solicitacao],
        foco: str | None = None,
    ) -> str:
        """Executa as operações e devolve o bloco serializado."""
        return self.serializar(self.executar(solicitacoes), foco)


def _para_chat(dados: object) -> object:
    """Adapta o resultado canônico do núcleo ao formato do bloco do chat.

    As listagens devolvem os itens diretamente (o chat não usa cursor) e as
    buscas descartam o ``nextCursor``, que é uma preocupação das superfícies
    paginadas (CLI e MCP).
    """
    if isinstance(dados, dict):
        if "itens" in dados:
            return dados["itens"]
        if "nextCursor" in dados:
            return {chave: valor for chave, valor in dados.items() if chave != "nextCursor"}
    return dados
