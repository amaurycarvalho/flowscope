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
from collections.abc import Iterator

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.chat import ConsultarChatUseCase
from flowscope.domain.llm import LLMError, LLMUnavailableError
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
        self._bloco_cache: tuple[str, str] | None = None
        self._enviando = False
        self._heartbeat_intervalo = HEARTBEAT_INTERVALO_S

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
        """Monta o contexto e consulta a LLM na thread de trabalho do job."""
        self._ctx_atual = ctx
        try:
            ctx.raise_if_cancelled()
            with self._heartbeat(ctx):
                contexto = self._contexto.montar(
                    pergunta, fundamentos, watchlist, cache=self._bloco_cache
                )
                self._bloco_cache = (contexto.assinatura, contexto.bloco_estavel)
                ctx.raise_if_cancelled()
                usecase = ConsultarChatUseCase(self._criar_llm())
                resposta = usecase.consultar(
                    pergunta,
                    contexto,
                    ctx.token,
                    historico,
                    ao_uso=lambda uso: ctx.progress(dados=uso),
                )
        except OperacaoCancelada:
            return
        except LLMUnavailableError as exc:
            ctx.erro(exc, dados="indisponivel")
        except LLMError as exc:
            ctx.erro(exc, dados="erro")
        except Exception as exc:
            ctx.erro(exc, dados="erro")
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

    def _confirmar_no_tk(
        self: "EnvioMixin", quantidade: int, nomes: list[str]
    ) -> bool:
        """Pede confirmação à interface e aguarda a resposta na thread de trabalho."""
        ctx = getattr(self, "_ctx_atual", None)
        if ctx is None or ctx.cancelled:
            return False
        return ctx.confirmar(quantidade, list(nomes), self._confirmation_timeout)

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
