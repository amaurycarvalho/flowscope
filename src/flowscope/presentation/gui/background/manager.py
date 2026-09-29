"""Gerenciador único de jobs assíncronos da interface.

Recebe um callable de trabalho, cria um job com token de cancelamento próprio,
aplica a política de agendamento do grupo e publica progresso, resultado, erro
e término por uma fila drenada em um único ponto na thread do Tk.
"""

import itertools
import logging
import queue
import threading
import time
from collections.abc import Callable

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Evento, Termino
from flowscope.presentation.gui.background.job import (
    Callback,
    EstadoJob,
    JobCallbacks,
    JobHandle,
    Politica,
    Trabalho,
)
from flowscope.presentation.gui.background.pump import Pump
from flowscope.presentation.gui.background.scheduler import Decisao, Scheduler

logger = logging.getLogger("flowscope")

#: Tempo máximo sem progresso antes de encerrar um job por inatividade.
LIMITE_INATIVIDADE_S = 120.0


class BackgroundManager:
    """Submete, agenda e cancela trabalhos assíncronos fora da thread do Tk."""

    def __init__(
        self: "BackgroundManager",
        agendar: Callable[[int, Callable[[], None]], object] | None = None,
        *,
        intervalo_ms: int = 50,
        limite_inatividade_s: float = LIMITE_INATIVIDADE_S,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        """Inicializa o gerenciador e, se houver, o pump da thread do Tk."""
        self._agendar = agendar
        self._relogio = relogio
        self._limite_inatividade_s = limite_inatividade_s
        self._scheduler = Scheduler()
        self._jobs: dict[int, JobHandle] = {}
        self._contador = itertools.count(1)
        self._listeners_iniciado: list[Callable[[JobHandle], None]] = []
        self._listeners_terminado: list[Callable[[JobHandle], None]] = []
        self._pump = (
            Pump(agendar, self.drenar, lambda: bool(self._jobs), intervalo_ms=intervalo_ms)
            if agendar is not None
            else None
        )

    @property
    def jobs_ativos(self: "BackgroundManager") -> tuple[JobHandle, ...]:
        """Retorna os jobs atualmente ativos."""
        return tuple(self._jobs.values())

    def job(self: "BackgroundManager", job_id: int) -> JobHandle | None:
        """Retorna o job ativo com o identificador informado."""
        return self._jobs.get(job_id)

    def tem_ativo(self: "BackgroundManager", grupo: str) -> bool:
        """Indica se o grupo possui um job ativo no agendador."""
        return self._scheduler.ativo(grupo) is not None

    def ao_iniciar(self: "BackgroundManager", callback: Callable[[JobHandle], None]) -> None:
        """Registra um callback chamado quando um job inicia."""
        self._listeners_iniciado.append(callback)

    def ao_terminar(self: "BackgroundManager", callback: Callable[[JobHandle], None]) -> None:
        """Registra um callback chamado quando um job termina."""
        self._listeners_terminado.append(callback)

    def submit(
        self: "BackgroundManager",
        trabalho: Trabalho,
        *,
        grupo: str = "geral",
        politica: Politica = Politica.PARALLEL,
        chave: object = None,
        cancelavel: bool = False,
        ao_progresso: Callback | None = None,
        ao_resultado: Callback | None = None,
        ao_erro: Callback | None = None,
        ao_termino: Callback | None = None,
    ) -> JobHandle:
        """Submete um trabalho e retorna o identificador do job."""
        handle = JobHandle(
            id=next(self._contador),
            grupo=grupo,
            politica=politica,
            chave=chave,
            cancelavel=cancelavel,
            callbacks=JobCallbacks(
                progresso=ao_progresso,
                resultado=ao_resultado,
                erro=ao_erro,
                termino=ao_termino,
            ),
            trabalho=trabalho,
        )
        decisao = self._scheduler.decidir(handle)
        if decisao is Decisao.DESCARTAR:
            handle.estado = EstadoJob.DESCARTADO
            return handle
        if decisao is Decisao.ENFILEIRAR:
            self._scheduler.enfileirar(handle)
            return handle
        if decisao is Decisao.SUBSTITUIR:
            # Inicia o substituto antes de finalizar o anterior para que a
            # contagem de operações ativas não atravesse o zero e os controles
            # não sejam restaurados entre as duas cargas.
            ativo = self._scheduler.ativo(handle.grupo)
            self._iniciar(handle)
            if ativo is not None:
                self.cancel(ativo.id)
            return handle
        self._iniciar(handle)
        return handle

    def cancel(self: "BackgroundManager", job_id: int) -> None:
        """Cancela e finaliza o job informado, sem afetar os demais."""
        handle = self._jobs.get(job_id)
        if handle is None:
            return
        handle.token.request()
        self._finalizar(handle, cancelado=True)

    def cancel_group(self: "BackgroundManager", grupo: str) -> None:
        """Cancela e finaliza todos os jobs ativos do grupo."""
        for pendente in self._scheduler.retirar_pendentes(grupo):
            pendente.estado = EstadoJob.DESCARTADO
        for handle in list(self._jobs.values()):
            if handle.grupo == grupo:
                self.cancel(handle.id)

    def cancel_all(self: "BackgroundManager") -> None:
        """Cancela e finaliza todos os jobs ativos."""
        for pendente in self._scheduler.limpar_pendentes():
            pendente.estado = EstadoJob.DESCARTADO
        for job_id in list(self._jobs):
            self.cancel(job_id)

    def drenar(self: "BackgroundManager") -> None:
        """Drena as filas dos jobs e aplica o watchdog na thread do Tk."""
        for handle in list(self._jobs.values()):
            self._drenar_handle(handle)
        self._aplicar_watchdog()

    def _iniciar(self: "BackgroundManager", handle: JobHandle) -> None:
        """Registra o job como ativo e inicia sua thread de trabalho."""
        self._scheduler.marcar_ativo(handle)
        handle.estado = EstadoJob.EXECUTANDO
        handle.ultima_atividade = self._relogio()
        self._jobs[handle.id] = handle
        thread = threading.Thread(
            target=self._trabalhar,
            args=(handle,),
            name=f"flowscope-bg-{handle.id}",
            daemon=True,
        )
        handle.thread = thread
        self._notificar(self._listeners_iniciado, handle)
        thread.start()
        if self._pump is not None:
            self._pump.garantir_ativo()

    def _trabalhar(self: "BackgroundManager", handle: JobHandle) -> None:
        """Executa o trabalho do job e publica o término na fila."""
        contexto = JobContext(handle, self._publicador(handle))
        try:
            if handle.trabalho is not None:
                handle.trabalho(contexto)
        except OperacaoCancelada:
            logger.debug("Job %s interrompido pelo usuário", handle.id)
        except Exception as exc:  # falha inesperada não deve travar a interface
            logger.warning("Falha no job %s", handle.id, exc_info=True)
            contexto.erro(exc)
        finally:
            handle.fila.put(Termino(cancelado=handle.token.is_set))

    def _publicador(
        self: "BackgroundManager", handle: JobHandle
    ) -> Callable[[Evento], None]:
        """Retorna a função de publicação que atualiza a atividade do job."""

        def publicar(evento: Evento) -> None:
            handle.ultima_atividade = self._relogio()
            handle.fila.put(evento)

        return publicar

    def _drenar_handle(self: "BackgroundManager", handle: JobHandle) -> None:
        """Consome a fila de um job até esvaziar ou encontrar o término."""
        while True:
            try:
                evento = handle.fila.get_nowait()
            except queue.Empty:
                return
            if isinstance(evento, Termino):
                self._despachar_termino(handle, evento)
                return
            self._despachar(handle, evento)

    def _despachar(self: "BackgroundManager", handle: JobHandle, evento: Evento) -> None:
        """Entrega um evento ao callback registrado do job."""
        callback = handle.callbacks.para(evento)
        if callback is None:
            return
        self._invocar(callback, evento)

    def _despachar_termino(
        self: "BackgroundManager", handle: JobHandle, evento: Termino
    ) -> None:
        """Entrega o término ao callback do job e o finaliza."""
        callback = handle.callbacks.termino
        if callback is not None:
            self._invocar(callback, evento)
        self._finalizar(handle, cancelado=evento.cancelado)

    def _finalizar(self: "BackgroundManager", handle: JobHandle, cancelado: bool) -> None:
        """Remove o job do registro, notifica o término e inicia o próximo."""
        if handle.estado in (
            EstadoJob.CONCLUIDO,
            EstadoJob.CANCELADO,
            EstadoJob.DESCARTADO,
        ):
            return
        handle.estado = EstadoJob.CANCELADO if cancelado else EstadoJob.CONCLUIDO
        self._jobs.pop(handle.id, None)
        self._scheduler.remover(handle)
        self._notificar(self._listeners_terminado, handle)
        if handle.politica is Politica.SERIALIZE:
            proximo = self._scheduler.retirar_proximo(handle.grupo)
            if proximo is not None:
                self._iniciar(proximo)

    def _aplicar_watchdog(self: "BackgroundManager") -> None:
        """Encerra jobs mortos sem término e jobs sem progresso por inatividade."""
        agora = self._relogio()
        for handle in list(self._jobs.values()):
            thread = handle.thread
            if (
                thread is not None
                and not thread.is_alive()
                and handle.fila.empty()
            ):
                self._finalizar(handle, cancelado=False)
                continue
            if agora - handle.ultima_atividade > self._limite_inatividade_s:
                handle.token.request()
                self._finalizar(handle, cancelado=True)

    def _invocar(self: "BackgroundManager", callback: Callback, evento: Evento) -> None:
        """Invoca um callback de evento tolerando falhas de renderização."""
        try:
            callback(evento)
        except Exception:  # erro de callback não deve interromper a drenagem
            logger.warning(
                "Falha ao tratar evento %s", type(evento).__name__, exc_info=True
            )

    def _notificar(
        self: "BackgroundManager",
        listeners: list[Callable[[JobHandle], None]],
        handle: JobHandle,
    ) -> None:
        """Invoca os listeners de ciclo de vida tolerando falhas individuais."""
        for listener in listeners:
            try:
                listener(handle)
            except Exception:  # listener não deve derrubar o gerenciador
                logger.warning(
                    "Falha em listener de ciclo de vida do job %s",
                    handle.id,
                    exc_info=True,
                )
