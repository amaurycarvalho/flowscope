"""Orquestração da cascata de chat sobre a porta ``LLMPort`` da llm-core.

Resolve cada pergunta em no máximo duas chamadas de completion: a primeira
com os resumos curtos e longos do escopo; a segunda, quando a LLM pedir
documentos-alvo, com o texto integral desses documentos. A resposta do modelo
é interpretada de forma tolerante, com fallback para o texto integral quando o
formato estruturado não é reconhecido.
"""

import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from flowscope.application.cancellation import CancellationToken
from flowscope.domain.chat import ChatMessage
from flowscope.domain.llm import LLMPort, LLMResposta, LLMUsage

#: Teto de turnos anteriores enviados à LLM.
HISTORICO_MAX_MENSAGENS = 10

#: Teto de caracteres do histórico de turnos anteriores enviado à LLM.
HISTORICO_MAX_CARACTERES = 8000

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

#: Callback notificado com o uso de tokens de cada completion da cascata.
AoUso = Callable[[LLMUsage], None]


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

    ``bloco_estavel`` é o prefixo cacheável (conhecimento, fundamentos e
    resumos) e ``assinatura`` identifica o seu conteúdo. ``fontes_adicionais``
    é o ponto de extensão para changes futuras (``noticias-b3``,
    ``llm-chat-rag``): cada fonte entra no sufixo volátil, sem alterar a ordem
    da cascata de documentos.
    """

    bloco_estavel: str = ""
    assinatura: str = ""
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


def _selecionar_historico(
    historico: Sequence[ChatMessage] | None,
) -> list[dict]:
    """Seleciona os turnos anteriores que compõem o histórico da LLM.

    Descarta as mensagens marcadas como fora do histórico (erros e avisos) e,
    quando o teto de mensagens ou de caracteres é excedido, remove os turnos
    mais antigos, preservando os mais recentes.
    """
    if not historico:
        return []
    elegiveis = [msg for msg in historico if msg.enviar_ao_modelo and msg.content]
    selecionadas: list[ChatMessage] = []
    total = 0
    for msg in reversed(elegiveis):
        if len(selecionadas) >= HISTORICO_MAX_MENSAGENS:
            break
        if total + len(msg.content) > HISTORICO_MAX_CARACTERES and selecionadas:
            break
        selecionadas.append(msg)
        total += len(msg.content)
    selecionadas.reverse()
    return [{"role": msg.role, "content": msg.content} for msg in selecionadas]


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
        historico: Sequence[ChatMessage] | None = None,
        ao_uso: AoUso | None = None,
    ) -> RespostaChat:
        """Consulta o contexto de resumos e escala para o texto integral se preciso."""
        self._checar(cancel_token)
        turnos = _selecionar_historico(historico)
        prefixo = self._montar_prefixo(contexto)
        primeira = self._completar(
            prefixo,
            self._montar_sufixo(pergunta, contexto.fontes_adicionais, None),
            turnos,
            ao_uso,
        )
        resposta = interpretar_resposta(primeira.texto)
        if not resposta.documentos_solicitados or contexto.documentos is None:
            return resposta
        return self._escalar(
            pergunta, contexto, resposta, prefixo, turnos, cancel_token, ao_uso
        )

    def _escalar(
        self: "ConsultarChatUseCase",
        pergunta: str,
        contexto: ContextoChat,
        resposta: RespostaChat,
        prefixo: str,
        historico: list[dict] | None = None,
        cancel_token: CancellationToken | None = None,
        ao_uso: AoUso | None = None,
    ) -> RespostaChat:
        """Executa a segunda chamada com o texto integral dos alvos.

        Reaproveita o mesmo prefixo estável e o mesmo histórico da primeira
        chamada; apenas o sufixo muda, acrescentando o texto integral.
        """
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
            prefixo,
            self._montar_sufixo(pergunta, [], texto_integral),
            historico or [],
            ao_uso,
        )
        final = interpretar_resposta(segunda.texto)
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

    def _completar(
        self: "ConsultarChatUseCase",
        prefixo: str,
        sufixo: str,
        historico: list[dict],
        ao_uso: AoUso | None = None,
    ) -> LLMResposta:
        """Envia o prefixo estável no sistema e o sufixo no turno atual."""
        mensagens = [*historico, {"role": "user", "content": sufixo}]
        resposta = self._llm.complete(
            mensagens,
            system_prompt=prefixo,
        )
        if ao_uso is not None:
            ao_uso(resposta.uso)
        return resposta

    def _montar_prefixo(
        self: "ConsultarChatUseCase", contexto: ContextoChat
    ) -> str:
        """Monta o prefixo estável: instruções e contexto cacheável."""
        partes = [self._system_prompt, INSTRUCAO_FORMATO]
        if contexto.bloco_estavel:
            partes.append(contexto.bloco_estavel)
        return "\n\n".join(partes)

    @staticmethod
    def _montar_sufixo(
        pergunta: str,
        fontes: Sequence[FonteContexto],
        texto_integral: str | None,
    ) -> str:
        """Monta o sufixo volátil: texto integral, fontes e pergunta atual."""
        partes: list[str] = []
        if texto_integral:
            partes.extend(
                ["## Texto integral dos documentos-alvo", texto_integral, ""]
            )
        for fonte in fontes:
            partes.extend([f"## {fonte.titulo}", fonte.texto, ""])
        partes.extend(["## Pergunta", pergunta])
        return "\n".join(partes)
