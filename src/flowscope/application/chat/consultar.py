"""Orquestração da cascata de chat sobre a porta ``LLMPort`` da llm-core.

Resolve cada pergunta em no máximo duas chamadas de completion: a primeira
com os resumos curtos e longos do escopo; a segunda, quando a LLM pedir
documentos-alvo, com o texto integral desses documentos. A resposta do modelo
é interpretada de forma tolerante, com fallback para o texto integral quando o
formato estruturado não é reconhecido.
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace

from flowscope.application.cancellation import CancellationToken
from flowscope.domain.llm import LLMPort

#: Prompt de sistema comum às duas chamadas.
SYSTEM_PROMPT = (
    "Você é o assistente do FlowScope, uma ferramenta de análise quantitativa "
    "de fluxo de ordens. Responda apenas com base no contexto fornecido. "
    "Cite as fontes usadas (tickers e documentos) na resposta. Identifique o "
    "ticker referido na pergunta a partir do texto dela; quando a pergunta for "
    "ambígua quanto ao ativo, peça esclarecimento em vez de adivinhar. Se o "
    "contexto não contiver informação suficiente, admita a limitação com "
    "clareza, sem inventar dados."
)

#: Instrução do contrato de resposta estruturada.
INSTRUCAO_FORMATO = (
    "Responda exclusivamente com um objeto JSON no formato "
    '{"resposta": "<texto>", "documentos": ["<chave>", ...]}. '
    'Deixe "documentos" vazio quando a resposta já estiver conclusiva. '
    "Preencha-o com as chaves de documentos cujo texto integral você precisa "
    "ler para responder."
)

#: Texto devolvido quando não há alvos suficientes para responder.
MENSAGEM_SEM_ALVO = (
    "Não encontrei documentos no contexto que bastem para responder com "
    "precisão."
)

_MARCADOR_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class RespostaChat:
    """Resposta do assistente com as fontes e os documentos solicitados."""

    texto: str
    fontes: list[str] = field(default_factory=list)
    documentos_solicitados: list[str] = field(default_factory=list)


@dataclass
class ContextoDocumental:
    """Contexto documental em cascata: resumos, leitura e confirmação."""

    resumos: str
    preparar_texto: Callable[[list[str]], str]
    confirmar: Callable[[list[str]], bool]


@dataclass(frozen=True)
class FonteContexto:
    """Fonte adicional de contexto, renderizada como seção própria no prompt."""

    titulo: str
    texto: str


@dataclass
class ContextoChat:
    """Contexto completo recebido pela LLM em uma pergunta.

    ``fontes_adicionais`` é o ponto de extensão para changes futuras
    (``noticias-b3``, ``llm-chat-rag``): cada fonte entra como uma seção
    própria, sem alterar a ordem da cascata de documentos.
    """

    conhecimento: str = ""
    fundamentos: str = ""
    documentos: ContextoDocumental | None = None
    fontes_adicionais: list[FonteContexto] = field(default_factory=list)


def _documentos_validos(valor: object) -> list[str]:
    """Normaliza a lista de chaves de documentos, descartando itens inválidos."""
    if not isinstance(valor, list):
        return []
    return [item for item in valor if isinstance(item, str) and item.strip()]


def _extrair_json(texto: str) -> dict | None:
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


def interpretar_resposta(resposta: str) -> RespostaChat:
    """Interpreta a resposta da LLM de forma tolerante.

    Quando o formato estruturado é reconhecido, extrai a resposta e as chaves
    de documentos-alvo; caso contrário, trata o texto inteiro como resposta e
    não dispara nova rodada.
    """
    dados = _extrair_json(resposta)
    if dados is not None:
        texto = dados.get("resposta")
        if isinstance(texto, str):
            documentos = _documentos_validos(dados.get("documentos"))
            return RespostaChat(
                texto=texto.strip(),
                fontes=documentos,
                documentos_solicitados=documentos,
            )
    return RespostaChat(texto=(resposta or "").strip())


class ConsultarChatUseCase:
    """Resolve uma pergunta do chat em até duas chamadas de completion."""

    def __init__(
        self: "ConsultarChatUseCase",
        llm: LLMPort,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        """Guarda a porta de completion e o prompt de sistema."""
        self._llm = llm
        self._system_prompt = system_prompt

    def consultar(
        self: "ConsultarChatUseCase",
        pergunta: str,
        contexto: ContextoChat,
        cancel_token: CancellationToken | None = None,
    ) -> RespostaChat:
        """Consulta o contexto de resumos e escala para o texto integral se preciso."""
        self._checar(cancel_token)
        primeira = self._completar(self._montar_prompt(pergunta, contexto, None))
        resposta = interpretar_resposta(primeira)
        if not resposta.documentos_solicitados or contexto.documentos is None:
            return resposta
        return self._escalar(pergunta, contexto, resposta, cancel_token)

    def _escalar(
        self: "ConsultarChatUseCase",
        pergunta: str,
        contexto: ContextoChat,
        resposta: RespostaChat,
        cancel_token: CancellationToken | None = None,
    ) -> RespostaChat:
        """Executa a segunda chamada com o texto integral dos alvos."""
        alvos = resposta.documentos_solicitados
        if not contexto.documentos.confirmar(alvos):
            return replace(
                resposta,
                texto=resposta.texto or MENSAGEM_SEM_ALVO,
            )
        self._checar(cancel_token)
        texto_integral = contexto.documentos.preparar_texto(alvos)
        self._checar(cancel_token)
        segunda = self._completar(
            self._montar_prompt(pergunta, contexto, texto_integral)
        )
        final = interpretar_resposta(segunda)
        return replace(
            final,
            fontes=final.documentos_solicitados or alvos,
            documentos_solicitados=[],
        )

    @staticmethod
    def _checar(cancel_token: CancellationToken | None) -> None:
        """Lança ``OperacaoCancelada`` quando o cancelamento foi solicitado."""
        if cancel_token is not None:
            cancel_token.raise_if_cancelled()

    def _completar(self: "ConsultarChatUseCase", prompt: str) -> str:
        """Envia o prompt como mensagem de usuário, com o sistema estável."""
        return self._llm.complete(
            [{"role": "user", "content": prompt}],
            system_prompt=self._system_prompt,
        )

    @staticmethod
    def _montar_prompt(
        pergunta: str, contexto: ContextoChat, texto_integral: str | None
    ) -> str:
        """Monta o prompt com o conhecimento, fundamentos e documentos."""
        partes = [INSTRUCAO_FORMATO, ""]
        if contexto.conhecimento:
            partes.extend(["## Conhecimento do FlowScope", contexto.conhecimento, ""])
        if contexto.fundamentos:
            partes.extend(["## Fundamentos carregados", contexto.fundamentos, ""])
        if contexto.documentos and contexto.documentos.resumos:
            partes.extend(
                [
                    "## Resumos de documentos",
                    contexto.documentos.resumos,
                    "",
                ]
            )
        if texto_integral:
            partes.extend(
                ["## Texto integral dos documentos-alvo", texto_integral, ""]
            )
        for fonte in contexto.fontes_adicionais:
            partes.extend([f"## {fonte.titulo}", fonte.texto, ""])
        partes.extend(["## Pergunta", pergunta])
        return "\n".join(partes)
