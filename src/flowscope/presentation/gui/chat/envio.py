"""Coordenação do envio em background do painel de chat.

O mixin concentra o ciclo de vida de um envio: thread de trabalho, fila de
desfecho, contador de geração e cancelamento cooperativo. O ``ChatPanel`` o
combina com a interface, delegando aqui a orquestração do processamento.
"""

import queue
import threading
import tkinter as tk

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.chat import ConsultarChatUseCase
from flowscope.domain.llm import LLMError, LLMUnavailableError

#: Mensagem exibida quando o envio é cancelado pelo usuário.
MENSAGEM_CANCELADO = "Envio cancelado."


class EnvioMixin:
    """Mixin com o envio, a fila de desfecho e o cancelamento do chat."""

    def _init_envio(self: "EnvioMixin") -> None:
        """Inicializa o estado do envio em background."""
        self._fila: queue.Queue = queue.Queue()
        self._processando = False
        self._cancel_token = CancellationToken()
        self._geracao = 0
        self._trabalhadores = 0
        self._poll_ativo = False

    def _on_return(self: "EnvioMixin", event: tk.Event) -> str:
        """Envia a pergunta ao pressionar Enter sem Shift."""
        if event.state & 0x1:
            return ""
        self._enviar()
        return "break"

    def _enviar(self: "EnvioMixin") -> None:
        """Registra a pergunta e inicia a consulta em thread de trabalho."""
        if self._processando or not self._disponivel:
            return
        pergunta = self._texto_entrada()
        if not pergunta:
            return
        self._texto_entrada_set("")
        self._registrar("user", pergunta)
        self._geracao += 1
        geracao = self._geracao
        self._cancel_token.clear()
        self._processando = True
        self._trabalhadores += 1
        self._atualizar_controles()
        self._status("Consultando a I.A.…", "")
        snapshot_f = dict(self._fundamental_data_provider() or {})
        snapshot_w = list(self._watchlist_provider() or [])
        threading.Thread(
            target=self._executar,
            args=(geracao, pergunta, snapshot_f, snapshot_w),
            daemon=True,
        ).start()
        self._iniciar_poll()

    def _iniciar_poll(self: "EnvioMixin") -> None:
        """Garante um único laço de consumo da fila na thread do Tk."""
        if self._poll_ativo:
            return
        self._poll_ativo = True
        self.after(20, self._poll)

    def _executar(
        self: "EnvioMixin",
        geracao: int,
        pergunta: str,
        fundamentos: dict,
        watchlist: list[str],
    ) -> None:
        """Monta o contexto e consulta a LLM em thread de trabalho."""
        try:
            self._cancel_token.raise_if_cancelled()
            contexto = self._montar_contexto(pergunta, fundamentos, watchlist)
            self._cancel_token.raise_if_cancelled()
            usecase = ConsultarChatUseCase(self._criar_llm())
            resposta = usecase.consultar(pergunta, contexto, self._cancel_token)
        except OperacaoCancelada:
            self._fila.put((geracao, "cancelado", None))
        except LLMUnavailableError as exc:
            self._fila.put((geracao, "indisponivel", exc))
        except LLMError as exc:
            self._fila.put((geracao, "erro", exc))
        except Exception as exc:
            self._fila.put((geracao, "erro", exc))
        else:
            self._fila.put((geracao, "ok", resposta))

    def _confirmar_no_tk(
        self: "EnvioMixin", quantidade: int, nomes: list[str]
    ) -> bool:
        """Pede confirmação na thread do Tk e aguarda a resposta na thread de trabalho."""
        if self._cancel_token.is_set:
            return False
        evento = threading.Event()
        caixa: dict = {}
        self._fila.put(("confirmar", quantidade, nomes, evento, caixa))
        evento.wait(self._confirmation_timeout)
        return bool(caixa.get("ok", False))

    def _poll(self: "EnvioMixin") -> None:
        """Consome a fila de resultados na thread do Tk."""
        try:
            mensagem = self._fila.get_nowait()
        except queue.Empty:
            if self._trabalhadores > 0:
                self.after(20, self._poll)
            else:
                self._poll_ativo = False
            return
        if mensagem[0] == "confirmar":
            self._atender_confirmacao(mensagem)
            self.after(10, self._poll)
            return
        geracao = mensagem[0]
        self._trabalhadores -= 1
        if geracao == self._geracao and self._processando:
            self._concluir(mensagem)
        if self._trabalhadores > 0:
            self.after(20, self._poll)
        else:
            self._poll_ativo = False

    def _cancelar_envio(self: "EnvioMixin") -> None:
        """Interrompe o envio corrente e restaura os controles de imediato.

        O desfecho tardio da thread de trabalho é descartado pelo contador de
        geração, sem ser exibido nem registrado.
        """
        if not self._processando:
            return
        self._cancel_token.request()
        self._processando = False
        self._atualizar_controles()
        self._status(MENSAGEM_CANCELADO, "")
