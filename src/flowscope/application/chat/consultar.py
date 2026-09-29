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

#: Chaves reservadas dos recursos iniciais servidos sob demanda.
RECURSO_CONHECIMENTO = "conhecimento"
RECURSO_FUNDAMENTOS = "fundamentos"
RECURSO_RESUMOS = "resumos"
RECURSOS_INICIAIS = (
    RECURSO_CONHECIMENTO,
    RECURSO_FUNDAMENTOS,
    RECURSO_RESUMOS,
)


def _instrucao_limitada(recursos: dict[str, str]) -> str:
    """Monta a instrução de formato informando as chaves de recurso disponíveis."""
    chaves = ", ".join(sorted(recursos))
    return (
        "Responda exclusivamente com um objeto JSON no formato "
        '{"resposta": "<texto>", "documentos": ["<chave>", ...]}. '
        'Deixe "documentos" vazio quando a resposta já estiver conclusiva. '
        "Os dados iniciais do FlowScope NÃO foram carregados por limitação de "
        "janela de entrada. Para carregá-los, preencha \"documentos\" com as "
        f"chaves de recurso necessárias: {chaves}. Você também pode incluir "
        "chaves de documentos cujo texto integral precise ler."
    )

_MARCADOR_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

#: Callback notificado com o uso de tokens de cada completion da cascata.
AoUso = Callable[[LLMUsage], None]

#: Contador determinístico de tokens de um texto.
ContarTokens = Callable[[str], int]


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
    prefixo_repetido: bool = False
    input_limitado: bool = False
    recursos: dict[str, str] = field(default_factory=dict)
    confirmar_recursos: Callable[[list[str]], bool] | None = None


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
        contar_tokens: ContarTokens | None = None,
        cache_suportado: bool = False,
    ) -> None:
        """Guarda a porta, o prompt, o contador de tokens e o suporte a cache."""
        self._llm = llm
        self._system_prompt = system_prompt
        self._contar_tokens = contar_tokens
        self._cache_suportado = cache_suportado
        self._prefixos_enviados: set[str] = set()
        self._cache_estimado: dict[str, int] = {}

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
            contexto.prefixo_repetido,
        )
        resposta = interpretar_resposta(primeira.texto)
        if not resposta.documentos_solicitados:
            return resposta
        if contexto.input_limitado:
            return self._escalar_sob_demanda(
                pergunta, contexto, resposta, prefixo, turnos, cancel_token, ao_uso
            )
        if contexto.documentos is None:
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
            contexto.prefixo_repetido,
        )
        final = interpretar_resposta(segunda.texto)
        return replace(
            final,
            fontes=final.documentos_solicitados or alvos,
            documentos_solicitados=[],
        )

    def _escalar_sob_demanda(
        self: "ConsultarChatUseCase",
        pergunta: str,
        contexto: ContextoChat,
        resposta: RespostaChat,
        prefixo: str,
        historico: list[dict] | None = None,
        cancel_token: CancellationToken | None = None,
        ao_uso: AoUso | None = None,
    ) -> RespostaChat:
        """Serve recursos iniciais e/ou documentos, admitindo até três chamadas.

        A primeira escalada carrega os recursos pedidos (e documentos, se
        houver); quando recursos foram carregados e a LLM então pede documentos,
        uma terceira chamada lê o texto integral.
        """
        recursos, documentos = self._separar_pedidos(
            resposta.documentos_solicitados, contexto
        )
        texto_recursos = self._preparar_recursos(contexto, recursos)
        texto_docs = self._preparar_documentos(contexto, documentos)
        if not texto_recursos and not texto_docs:
            return replace(resposta, texto=resposta.texto or MENSAGEM_SEM_ALVO)
        self._checar(cancel_token)
        segunda = self._completar(
            prefixo,
            self._montar_sufixo(
                pergunta,
                [],
                texto_docs or None,
                texto_recursos or None,
            ),
            historico or [],
            ao_uso,
            contexto.prefixo_repetido,
        )
        intermediaria = interpretar_resposta(segunda.texto)
        terceira = self._preparar_terceira(
            contexto, intermediaria, texto_recursos
        )
        if terceira is not None:
            alvos, texto_docs2 = terceira
            return self._escalar_documentos(
                pergunta,
                contexto,
                alvos,
                texto_docs2,
                prefixo,
                historico,
                cancel_token,
                ao_uso,
            )
        return replace(
            intermediaria,
            fontes=intermediaria.documentos_solicitados or documentos,
            documentos_solicitados=[],
        )

    @staticmethod
    def _separar_pedidos(
        pedidos: list[str], contexto: ContextoChat
    ) -> tuple[list[str], list[str]]:
        """Separa as chaves pedidas em recursos iniciais e documentos."""
        recursos = [chave for chave in pedidos if chave in contexto.recursos]
        documentos = [chave for chave in pedidos if chave not in contexto.recursos]
        return recursos, documentos

    def _preparar_terceira(
        self: "ConsultarChatUseCase",
        contexto: ContextoChat,
        intermediaria: RespostaChat,
        texto_recursos: str,
    ) -> tuple[list[str], str] | None:
        """Prepara a terceira chamada quando a resposta pede documentos.

        Só se aplica quando recursos foram carregados e a LLM então indica
        documentos-alvo; devolve ``None`` quando não há terceira chamada.
        """
        if not texto_recursos or not intermediaria.documentos_solicitados:
            return None
        if contexto.documentos is None:
            return None
        alvos = intermediaria.documentos_solicitados
        texto_docs = self._preparar_documentos(contexto, alvos)
        if not texto_docs:
            return None
        return alvos, texto_docs

    def _escalar_documentos(
        self: "ConsultarChatUseCase",
        pergunta: str,
        contexto: ContextoChat,
        alvos: list[str],
        texto_docs: str,
        prefixo: str,
        historico: list[dict] | None,
        cancel_token: CancellationToken | None,
        ao_uso: AoUso | None,
    ) -> RespostaChat:
        """Executa a terceira chamada com o texto integral dos documentos."""
        self._checar(cancel_token)
        terceira = self._completar(
            prefixo,
            self._montar_sufixo(pergunta, [], texto_docs, None),
            historico or [],
            ao_uso,
            contexto.prefixo_repetido,
        )
        final = interpretar_resposta(terceira.texto)
        return replace(
            final,
            fontes=final.documentos_solicitados or alvos,
            documentos_solicitados=[],
        )

    def _preparar_recursos(
        self: "ConsultarChatUseCase",
        contexto: ContextoChat,
        chaves: list[str],
    ) -> str:
        """Confirma e resolve os recursos iniciais pedidos, omitindo os vazios."""
        if not chaves:
            return ""
        confirmar = contexto.confirmar_recursos
        if confirmar is not None and not confirmar(list(chaves)):
            return ""
        partes = [
            contexto.recursos[chave]
            for chave in chaves
            if contexto.recursos.get(chave)
        ]
        return "\n\n".join(partes)

    def _preparar_documentos(
        self: "ConsultarChatUseCase",
        contexto: ContextoChat,
        chaves: list[str],
    ) -> str:
        """Confirma e resolve o texto integral dos documentos pedidos."""
        if not chaves or contexto.documentos is None:
            return ""
        if not contexto.documentos.confirmar(chaves):
            return ""
        return contexto.documentos.preparar_texto(chaves)

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
        prefixo_repetido: bool = False,
    ) -> LLMResposta:
        """Envia o prefixo estável no sistema e o sufixo no turno atual."""
        mensagens = [*historico, {"role": "user", "content": sufixo}]
        resposta = self._llm.complete(
            mensagens,
            system_prompt=prefixo,
        )
        uso = self._ajustar_uso(resposta.uso, prefixo, prefixo_repetido)
        if ao_uso is not None:
            ao_uso(uso)
        return replace(resposta, uso=uso)

    def _ajustar_uso(
        self: "ConsultarChatUseCase",
        uso: LLMUsage,
        prefixo: str,
        prefixo_repetido: bool,
    ) -> LLMUsage:
        """Estima o cache-hit do prefixo quando o provedor não o reporta.

        Só estima com um contador injetado, provedor que suporta cache e o
        prefixo já enviado (idêntico ao de uma completion anterior). O valor é
        memoizado por prefixo para não recontar a cada turno.
        """
        ja_enviado = prefixo in self._prefixos_enviados
        self._prefixos_enviados.add(prefixo)
        if uso.entrada_cache > 0:
            return uso
        if self._contar_tokens is None or not self._cache_suportado:
            return uso
        if not prefixo_repetido and not ja_enviado:
            return uso
        estimado = self._cache_estimado.get(prefixo)
        if estimado is None:
            estimado = max(0, int(self._contar_tokens(prefixo)))
            self._cache_estimado[prefixo] = estimado
        if estimado <= 0:
            return uso
        return replace(uso, entrada_cache=estimado)

    def _montar_prefixo(
        self: "ConsultarChatUseCase", contexto: ContextoChat
    ) -> str:
        """Monta o prefixo estável: instruções e contexto cacheável."""
        partes = [self._system_prompt]
        if contexto.input_limitado and contexto.recursos:
            partes.append(_instrucao_limitada(contexto.recursos))
        else:
            partes.append(INSTRUCAO_FORMATO)
        if contexto.bloco_estavel:
            partes.append(contexto.bloco_estavel)
        return "\n\n".join(partes)

    @staticmethod
    def _montar_sufixo(
        pergunta: str,
        fontes: Sequence[FonteContexto],
        texto_integral: str | None,
        texto_recursos: str | None = None,
    ) -> str:
        """Monta o sufixo volátil: recursos, texto integral, fontes e pergunta."""
        partes: list[str] = []
        if texto_recursos:
            partes.extend(["## Recursos iniciais", texto_recursos, ""])
        if texto_integral:
            partes.extend(
                ["## Texto integral dos documentos-alvo", texto_integral, ""]
            )
        for fonte in fontes:
            partes.extend([f"## {fonte.titulo}", fonte.texto, ""])
        partes.extend(["## Pergunta", pergunta])
        return "\n".join(partes)
