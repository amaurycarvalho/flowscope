"""Loop de navegação do chat sobre a árvore de conhecimento.

Resolve cada pergunta em até 10 ciclos sobre a porta ``LLMPort``: envia a
completion, interpreta o JSON tolerante, executa as operações de navegação e
devolve o resultado no ciclo seguinte até a resposta ser conclusiva. O prefixo
estável (manifesto) e o histórico são compartilhados por todos os ciclos; a
navegação fica em cota própria, reusada entre perguntas.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from flowscope.application.cancellation import CancellationToken
from flowscope.application.chat.arvore import ArvoreConhecimento
from flowscope.application.chat.manifesto import montar_manifesto
from flowscope.application.chat.protocolo import (
    ProtocoloNavegacao,
    RespostaProtocolo,
    interpretar,
)
from flowscope.domain.chat import ChatMessage
from flowscope.domain.llm import LLMPort, LLMResposta, LLMUsage

#: Teto de mensagens do diálogo enviadas à LLM.
HISTORICO_MAX_MENSAGENS = 10

#: Teto de caracteres do diálogo enviado à LLM.
HISTORICO_MAX_CARACTERES = 8000

#: Máximo de ciclos do loop de navegação.
MAX_ITERACOES = 10

#: Teto de tokens de navegação por turno antes de pedir autorização.
TETO_NAVEGACAO_TURNO = 64000

#: Cota acumulada de tokens de navegação reusada entre perguntas.
COTA_NAVEGACAO = 32000

#: Fração da janela do modelo que dispara o alerta de contexto total.
FRACAO_ALERTA_JANELA = 0.8

#: Razão grosseira de caracteres por token para estimativas sem contador.
CARACTERES_POR_TOKEN = 4

#: Prompt de sistema do loop de navegação.
SYSTEM_PROMPT = (
    "Você é o assistente do FlowScope, uma ferramenta de análise quantitativa de "
    "fluxo de ordens. Responda apenas com base no contexto navegado. Cite as "
    "fontes (tickers, chaves de notícia, caminhos). Identifique o ticker referido "
    "na pergunta; quando for ambíguo, peça esclarecimento. Use contar/existe antes "
    "de listar ramos grandes; quando a busca semântica não estiver disponível, use "
    "a busca determinística por regex (buscar) em vez de listar. Para comentar ou "
    "analisar um documento específico, leia o texto integral do alvo (ex.: "
    "/documentos/<ticker>/<chave>/texto); para textos longos, leia em páginas "
    "sucessivas via obter com offset/limite até `continua` ser falso. Para "
    "listar ou resumir vários "
    "documentos, abra o resumo curto (/curto) ou o resumo longo (/longo) de "
    "cada documento — o índice traz só uma prévia. Nunca responda prometendo "
    "navegar: se faltam dados, emita solicitacoes com resposta null e só "
    "finalize quando tiver o conteúdo. Use o foco para 'esse documento'. "
    "Declare quando a resposta vier de navegação anterior e não do estado corrente. "
    "Se o contexto não bastar, admita a limitação."
)

#: Instrução do contrato de resposta e das operações.
INSTRUCAO_FORMATO = (
    "Responda exclusivamente com um objeto JSON no formato "
    '{"resposta": "<texto ou null>", "solicitacoes": [{"op": "...", ...}]}. '
    "Deixe `solicitacoes` vazio quando a resposta já for conclusiva. Caso "
    "contrário, preencha-o com as operações de navegação necessárias."
)

#: Assinatura do callback notificado com o uso de cada completion.
AoUso = Callable[[LLMUsage], None]

#: Contador determinístico de tokens de um texto.
ContarTokens = Callable[[str], int]

#: Callback que confirma o custo adicional de um turno de navegação.
ConfirmarCusto = Callable[[int], bool]


@dataclass(frozen=True)
class ParNavegacao:
    """Par assistant/resultado da navegação, reusado entre perguntas."""

    assistant: str
    resultado: str

    @property
    def tokens(self: ParNavegacao) -> int:
        """Soma grosseira de tokens do par."""
        return (len(self.assistant) + len(self.resultado)) // CARACTERES_POR_TOKEN


@dataclass(frozen=True)
class RespostaChat:
    """Resposta final com as fontes e a navegação acumulada."""

    texto: str
    fontes: list[str] = field(default_factory=list)
    navegacao: list[ParNavegacao] = field(default_factory=list)
    alerta_janela: bool = False


def _selecionar_historico(historico: Sequence[ChatMessage] | None) -> list[dict]:
    """Seleciona os turnos de diálogo, descartando erros e avisos e os antigos."""
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


def _mensagens_navegacao(pares: Sequence[ParNavegacao]) -> list[dict]:
    """Achata os pares de navegação em mensagens assistant/user."""
    mensagens: list[dict] = []
    for par in pares:
        mensagens.append({"role": "assistant", "content": par.assistant})
        mensagens.append({"role": "user", "content": par.resultado})
    return mensagens


def _negativa(motivo: str, tokens: int) -> str:
    """Serializa a negativa estruturada devolvida à LLM."""
    return json.dumps(
        {"negado": True, "motivo": motivo, "tokens_solicitados": tokens},
        ensure_ascii=False,
    )


def _serializar_solicitacoes(interpretada: RespostaProtocolo) -> str:
    """Serializa as solicitações da resposta para o turno do assistant."""
    return json.dumps(
        {
            "resposta": interpretada.resposta,
            "solicitacoes": [
                {"op": s.op, **s.campos} for s in interpretada.solicitacoes
            ],
        },
        ensure_ascii=False,
    )


class ConsultarChatUseCase:
    """Resolve uma pergunta por um loop de navegação de até 10 ciclos."""

    def __init__(
        self: ConsultarChatUseCase,
        llm: LLMPort,
        system_prompt: str = SYSTEM_PROMPT,
        contar_tokens: ContarTokens | None = None,
        cache_suportado: bool = False,
        max_iteracoes: int = MAX_ITERACOES,
        teto_turno: int = TETO_NAVEGACAO_TURNO,
        cota_navegacao: int = COTA_NAVEGACAO,
        janela: int = 0,
        max_operacoes: int = 8,
    ) -> None:
        """Guarda a porta, os limites e o contador de tokens."""
        self._llm = llm
        self._system_prompt = system_prompt
        self._contar_tokens = contar_tokens
        self._cache_suportado = cache_suportado
        self._max_iteracoes = max_iteracoes
        self._teto_turno = teto_turno
        self._cota_navegacao = cota_navegacao
        self._janela = janela
        self._max_operacoes = max_operacoes
        self._prefixos_enviados: set[str] = set()
        self._cache_estimado: dict[str, int] = {}

    def consultar(
        self: ConsultarChatUseCase,
        pergunta: str,
        arvore: ArvoreConhecimento,
        historico: Sequence[ChatMessage] | None = None,
        navegacao: Sequence[ParNavegacao] | None = None,
        cancel_token: CancellationToken | None = None,
        ao_uso: AoUso | None = None,
        confirmar: ConfirmarCusto | None = None,
    ) -> RespostaChat:
        """Executa o loop de navegação e devolve a resposta final."""
        self._checar(cancel_token)
        protocolo = ProtocoloNavegacao(arvore, self._max_operacoes)
        prefixo = self._montar_prefixo(arvore)
        dialogo = _selecionar_historico(historico)
        acumulada = self._selecionar_navegacao(navegacao)
        estado = _Estado(prefixo=prefixo, dialogo=dialogo, pergunta=pergunta,
                         acumulada=acumulada, protocolo=protocolo,
                         ao_uso=ao_uso, confirmar=confirmar)
        for _ciclo in range(self._max_iteracoes):
            self._checar(cancel_token)
            resposta = self._completar(estado.prefixo, estado.mensagens(), ao_uso)
            self._atualizar_alerta(estado, resposta)
            interpretada = interpretar(resposta.texto)
            if interpretada.final:
                return self._resposta_final(estado, interpretada.resposta or "")
            self._processar_ciclo(estado, interpretada)
        return self._resumo_final(estado, cancel_token)

    # ── Ciclo ────────────────────────────────────────────────────────

    def _processar_ciclo(
        self: ConsultarChatUseCase, estado: _Estado, interpretada: RespostaProtocolo
    ) -> None:
        """Aplica gates, executa as operações e acumula o par de navegação."""
        tokens = self._tokens_solicitacoes(interpretada)
        assinatura = _assinatura_pedido(interpretada)
        if tokens > self._teto_turno and not self._confirmar_custo(estado, tokens):
            resultado = _negativa("custo", tokens)
            estado.negados.add(assinatura)
        elif assinatura in estado.negados:
            resultado = _negativa("custo", tokens)
        else:
            _aplicar_reset(estado, interpretada)
            resultados = estado.protocolo.executar(interpretada.solicitacoes)
            estado.fontes.extend(_fontes(resultados))
            estado.foco = _atualizar_foco(estado.foco, resultados)
            resultado = estado.protocolo.serializar(resultados, estado.foco)
        estado.correntes.append(
            ParNavegacao(_serializar_solicitacoes(interpretada), resultado)
        )

    @staticmethod
    def _confirmar_custo(estado: _Estado, tokens: int) -> bool:
        """Pede autorização do custo do turno, prosseguindo sem callback."""
        if estado.confirmar is None:
            return True
        return bool(estado.confirmar(tokens))

    def _resumo_final(
        self: ConsultarChatUseCase,
        estado: _Estado,
        cancel_token: CancellationToken | None,
    ) -> RespostaChat:
        """Força o resumo final ao esgotar as iterações."""
        self._checar(cancel_token)
        mensagens = [
            *estado.mensagens(),
            {"role": "user", "content": "Limite de iterações atingido. Resuma o que já foi navegado."},
        ]
        resposta = self._completar(estado.prefixo, mensagens, estado.ao_uso)
        return self._resposta_final(estado, resposta.texto.strip())

    def _resposta_final(
        self: ConsultarChatUseCase, estado: _Estado, texto: str
    ) -> RespostaChat:
        """Monta a resposta final com fontes, navegação e alerta de janela."""
        return RespostaChat(
            texto=texto,
            fontes=estado.fontes,
            navegacao=[*estado.acumulada, *estado.correntes],
            alerta_janela=estado.alerta,
        )

    # ── Cota e tokens ────────────────────────────────────────────────

    def _selecionar_navegacao(
        self: ConsultarChatUseCase, pares: Sequence[ParNavegacao] | None
    ) -> list[ParNavegacao]:
        """Seleciona os pares mais recentes que cabem na cota de navegação."""
        if not pares:
            return []
        selecionados: list[ParNavegacao] = []
        total = 0
        for par in reversed(pares):
            custo = self._tokens(par.assistant) + self._tokens(par.resultado)
            if selecionados and total + custo > self._cota_navegacao:
                break
            selecionados.append(par)
            total += custo
        selecionados.reverse()
        return selecionados

    def _atualizar_alerta(
        self: ConsultarChatUseCase, estado: _Estado, resposta: LLMResposta
    ) -> None:
        """Marca o alerta quando o prompt excede 80% da janela do modelo."""
        if self._janela and resposta.uso.entrada > self._janela * FRACAO_ALERTA_JANELA:
            estado.alerta = True

    def _tokens_solicitacoes(self: ConsultarChatUseCase, interpretada: RespostaProtocolo) -> int:
        """Estima os tokens das solicitações de um turno."""
        return self._tokens(_serializar_solicitacoes(interpretada))

    def _tokens(self: ConsultarChatUseCase, texto: str) -> int:
        """Conta (ou estima) os tokens de um texto."""
        if self._contar_tokens is not None:
            return int(self._contar_tokens(texto))
        return len(texto) // CARACTERES_POR_TOKEN

    # ── Prompt e completion ──────────────────────────────────────────

    def _montar_prefixo(self: ConsultarChatUseCase, arvore: ArvoreConhecimento) -> str:
        """Monta o prefixo estável: instruções e manifesto da árvore."""
        manifesto = montar_manifesto(arvore, contar_tokens=self._contar_tokens)
        return f"{self._system_prompt}\n\n{INSTRUCAO_FORMATO}\n\n{manifesto}"

    def _completar(
        self: ConsultarChatUseCase,
        prefixo: str,
        mensagens: list[dict],
        ao_uso: AoUso | None,
    ) -> LLMResposta:
        """Envia a completion com o prefixo estável e ajusta o uso de cache."""
        resposta = self._llm.complete(mensagens, system_prompt=prefixo)
        uso = self._ajustar_uso(resposta.uso, prefixo)
        if ao_uso is not None:
            ao_uso(uso)
        return replace(resposta, uso=uso)

    def _ajustar_uso(
        self: ConsultarChatUseCase, uso: LLMUsage, prefixo: str
    ) -> LLMUsage:
        """Estima o cache-hit do prefixo quando o provedor não o reporta."""
        ja_enviado = prefixo in self._prefixos_enviados
        self._prefixos_enviados.add(prefixo)
        if uso.entrada_cache > 0:
            return uso
        if self._contar_tokens is None or not self._cache_suportado or not ja_enviado:
            return uso
        estimado = self._cache_estimado.get(prefixo)
        if estimado is None:
            estimado = max(0, int(self._contar_tokens(prefixo)))
            self._cache_estimado[prefixo] = estimado
        if estimado <= 0:
            return uso
        return replace(uso, entrada_cache=estimado)

    @staticmethod
    def _checar(cancel_token: CancellationToken | None) -> None:
        """Lança ``OperacaoCancelada`` quando o cancelamento foi solicitado."""
        if cancel_token is not None:
            cancel_token.raise_if_cancelled()


@dataclass
class _Estado:
    """Estado mutável de uma consulta do loop de navegação."""

    prefixo: str
    dialogo: list[dict]
    pergunta: str
    acumulada: list[ParNavegacao]
    protocolo: ProtocoloNavegacao
    ao_uso: AoUso | None = None
    confirmar: ConfirmarCusto | None = None
    correntes: list[ParNavegacao] = field(default_factory=list)
    fontes: list[str] = field(default_factory=list)
    negados: set[str] = field(default_factory=set)
    alerta: bool = False
    foco: str | None = None

    def mensagens(self: _Estado) -> list[dict]:
        """Monta o payload: diálogo, navegação acumulada e o turno corrente."""
        return [
            *self.dialogo,
            *_mensagens_navegacao(self.acumulada),
            {"role": "user", "content": self.pergunta},
            *_mensagens_navegacao(self.correntes),
        ]


def _assinatura_pedido(interpretada: RespostaProtocolo) -> str:
    """Assinatura determinística de um pedido, para recusar repetições."""
    return json.dumps(
        [{"op": s.op, **s.campos} for s in interpretada.solicitacoes],
        ensure_ascii=False,
        sort_keys=True,
    )


def _fontes(resultados: list[dict]) -> list[str]:
    """Extrai os caminhos citados nos resultados de navegação."""
    fontes: list[str] = []
    for resultado in resultados:
        dados = resultado.get("dados")
        if isinstance(dados, list):
            fontes.extend(
                item["caminho"] for item in dados if isinstance(item, dict) and "caminho" in item
            )
    return fontes


def _atualizar_foco(foco: str | None, resultados: list[dict]) -> str | None:
    """Atualiza o foco com o último ``obter`` bem-sucedido do turno."""
    for resultado in resultados:
        if (
            resultado.get("op") == "obter"
            and resultado.get("caminho")
            and "dados" in resultado
            and "erro" not in resultado
        ):
            foco = resultado["caminho"]
    return foco


def _aplicar_reset(estado: _Estado, interpretada: RespostaProtocolo) -> None:
    """Descarta a navegação acumulada e o foco quando a LLM pede reset."""
    if any(solicitacao.op == "resetar_navegacao" for solicitacao in interpretada.solicitacoes):
        estado.acumulada.clear()
        estado.foco = None
