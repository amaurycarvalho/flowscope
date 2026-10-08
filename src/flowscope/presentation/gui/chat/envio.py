"""Coordenação do envio em background do painel de chat.

O mixin delega o ciclo de vida de cada envio a um ``BackgroundManager`` **local
ao painel**: o manager drena os eventos na thread do Tk, o token de cancelamento
é por job e a política ``latest_wins`` descarta o desfecho tardio de uma
consulta substituída. O handshake de confirmação de leitura usa o evento
``Confirmacao`` do manager, atendido na thread do Tk. Usar um manager local (e
nunca o global de ``app_wiring``) preserva o cursor e os botões da janela.
"""

import contextlib
import threading
import tkinter as tk
from collections.abc import Callable, Iterator

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.chat import ConsultarChatUseCase
from flowscope.domain.llm import LLMError, LLMUnavailableError, LLMUsage
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.background.manager import BackgroundManager

#: Mensagem exibida quando o envio é cancelado pelo usuário.
MENSAGEM_CANCELADO = "Envio cancelado."

#: Grupo de agendamento do envio do chat no manager local do painel.
GRUPO_CHAT = "chat"

#: Intervalo do heartbeat que mantém o job vivo durante chamadas longas.
HEARTBEAT_INTERVALO_S = 30.0


class EnvioMixin:
    """Mixin com o envio gerenciado e o cancelamento do chat."""

    def _init_envio(self: "EnvioMixin") -> None:
        """Inicializa o manager local do painel e o estado do envio."""
        self._background = BackgroundManager(self.after)
        self._background.ao_iniciar(lambda _handle: self._on_job_iniciado())
        self._background.ao_terminar(lambda _handle: self._on_job_terminado())
        self._ctx_atual: JobContext | None = None
        self._enviando = False
        self._heartbeat_intervalo = HEARTBEAT_INTERVALO_S

    def _contar_tokens(self: "EnvioMixin") -> Callable[[str], int] | None:
        """Obtém o contador de tokens do provedor ativo, tolerando ausência."""
        provider = getattr(self, "_token_counter_provider", None)
        if provider is None:
            return None
        try:
            return provider()
        except Exception:
            return None

    def _cache_suportado(self: "EnvioMixin") -> bool:
        """Indica se o provedor ativo suporta cache de prompt."""
        provider = getattr(self, "_cache_support_provider", None)
        if provider is None:
            return False
        try:
            return bool(provider())
        except Exception:
            return False

    def _janela_contexto(self: "EnvioMixin") -> int:
        """Obtém a janela de contexto do modelo ativo, ou zero se desconhecida."""
        provider = getattr(self, "_context_window_provider", None)
        if provider is None:
            return 0
        try:
            return int(provider())
        except Exception:
            return 0

    def _acumular_uso(self: "EnvioMixin", uso: object) -> None:
        """Soma o uso de uma completion ao total da sessão e publica o rótulo."""
        if not isinstance(uso, LLMUsage):
            return
        self._tokens.acumular(uso)
        self._publicar_tokens()

    def _publicar_tokens(self: "EnvioMixin") -> None:
        """Publica o total acumulado no rótulo persistente, quando houver."""
        callback = getattr(self, "_tokens_callback", None)
        if callback is not None:
            callback(self._tokens.texto(self._janela_contexto()))

    def _on_job_iniciado(self: "EnvioMixin") -> None:
        """Fecha a janela de envio assim que o job entra no manager."""
        self._enviando = False
        self._atualizar_controles()

    def _on_job_terminado(self: "EnvioMixin") -> None:
        """Restaura os controles ao término real do job."""
        self._enviando = False
        self._atualizar_controles()

    @property
    def _processando(self: "EnvioMixin") -> bool:
        """Indica se há um envio em curso ou um job ativo no manager.

        O estado ``_enviando`` cobre a janela entre registrar a pergunta e
        submeter o trabalho, de modo que os controles nunca vejam
        ``_processando`` falso nesse intervalo.
        """
        return self._enviando or self._background.tem_ativo(GRUPO_CHAT)

    def _on_return(self: "EnvioMixin", event: tk.Event) -> str:
        """Envia a pergunta ao pressionar Enter sem Shift."""
        if event.state & 0x1:
            return ""
        self._enviar()
        return "break"

    def _enviar(self: "EnvioMixin") -> None:
        """Registra a pergunta e submete a consulta ao manager local."""
        if self._processando or not self._disponivel:
            return
        pergunta = self._texto_entrada()
        if not pergunta:
            return
        self._texto_entrada_set("")
        historico = list(self._sessao.messages)
        self._enviando = True
        self._registrar("user", pergunta)
        self._status("Consultando a I.A.…", "")
        snapshot_f = dict(self._fundamental_data_provider() or {})
        snapshot_w = list(self._watchlist_provider() or [])
        self._background.submit(
            lambda ctx: self._executar(
                ctx, pergunta, snapshot_f, snapshot_w, historico
            ),
            grupo=GRUPO_CHAT,
            politica=Politica.LATEST_WINS,
            cancelavel=True,
            ao_progresso=lambda evento: self._acumular_uso(evento.dados),
            ao_resultado=lambda evento: self._concluir_ok(evento.valor),
            ao_erro=lambda evento: self._concluir_erro(
                evento.dados, evento.excecao
            ),
            ao_evento=self._atender_confirmacao,
        )

    def _executar(
        self: "EnvioMixin",
        ctx: JobContext,
        pergunta: str,
        fundamentos: dict,
        watchlist: list[str],
        historico: list,
    ) -> None:
        """Monta a árvore de conhecimento e consulta a LLM na thread de trabalho."""
        self._ctx_atual = ctx
        try:
            ctx.raise_if_cancelled()
            with self._heartbeat(ctx):
                arvore = self.montar_arvore(fundamentos, watchlist)
                if self._assinatura is not None and self._assinatura != arvore.assinatura:
                    self._navegacao = []
                self._assinatura = arvore.assinatura
                ctx.raise_if_cancelled()
                usecase = ConsultarChatUseCase(
                    self._criar_llm(),
                    contar_tokens=self._contar_tokens(),
                    cache_suportado=self._cache_suportado(),
                    janela=self._janela_contexto(),
                )
                resposta = usecase.consultar(
                    pergunta,
                    arvore,
                    historico=historico,
                    navegacao=list(self._navegacao),
                    cancel_token=ctx.token,
                    ao_uso=lambda uso: ctx.progress(dados=uso),
                    confirmar=self._confirmar_no_tk,
                )
        except OperacaoCancelada:
            return
        except LLMUnavailableError as exc:
            ctx.falhar(exc, dados="indisponivel")
        except LLMError as exc:
            ctx.falhar(exc, dados="erro")
        except Exception as exc:
            ctx.falhar(exc, dados="erro")
        else:
            ctx.resultado(valor=resposta)

    @contextlib.contextmanager
    def _heartbeat(self: "EnvioMixin", ctx: JobContext) -> Iterator[None]:
        """Publica progresso periódico enquanto o envio estiver em andamento.

        Mantém ``ultima_atividade`` fresco durante chamadas longas e a espera da
        confirmação, evitando que o watchdog encerre o job por inatividade. O
        pulso para assim que o bloco termina, sem manter o job vivo se o worker
        morrer.
        """
        parar = threading.Event()

        def pulsar() -> None:
            while not parar.wait(self._heartbeat_intervalo):
                try:
                    ctx.progress()
                except Exception:  # publicação não pode derrubar o heartbeat
                    return

        thread = threading.Thread(
            target=pulsar, name="flowscope-chat-heartbeat", daemon=True
        )
        thread.start()
        try:
            yield
        finally:
            parar.set()
            thread.join(timeout=1.0)

    def _confirmar_no_tk(self: "EnvioMixin", tokens: int) -> bool:
        """Autoriza o custo do turno na interface, aguardando na thread de trabalho."""
        ctx = getattr(self, "_ctx_atual", None)
        if ctx is None or ctx.cancelled:
            return False
        return ctx.confirmar(
            tokens,
            [],
            self._confirmation_timeout,
            motivo="custo",
        )

    def _cancelar_envio(self: "EnvioMixin") -> None:
        """Interrompe o envio corrente e restaura os controles de imediato.

        O desfecho tardio da thread de trabalho é descartado pela política
        ``latest_wins`` do manager, sem ser exibido nem registrado.
        """
        if not self._processando:
            return
        self._background.cancel_group(GRUPO_CHAT)
        self._atualizar_controles()
        self._status(MENSAGEM_CANCELADO, "")
