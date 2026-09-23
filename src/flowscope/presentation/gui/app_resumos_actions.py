"""Orquestração do resumo em lote dos documentos pendentes.

O mixin conduz o job de resumo em thread, drenando a fila na thread do Tk,
traduzindo o progresso para a barra de status e aplicando os resultados no
painel de documentos. Vive separado de :mod:`app_actions` para manter a
complexidade e o tamanho de cada módulo sob controle.
"""

import logging
import queue
import time

from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.progress import ProgressReporter
from flowscope.presentation.gui.resumos_job import (
    MENSAGEM_ERRO,
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    ResumosPendentesJob,
)

logger = logging.getLogger("flowscope")

#: Tempo mínimo de exibição de cada fase do lote de resumos.
_FASE_RESUMOS_MINIMA_S = 0.4


class ResumosActionsMixin:
    """Conduz o resumo em lote dos documentos pendentes do ticker."""

    def _resumos_em_andamento(self: "ResumosActionsMixin") -> bool:
        """Indica se há um resumo em lote em andamento."""
        return getattr(self, "_resumos_job", None) is not None

    def _resumir_documentos_pendentes(self: "ResumosActionsMixin") -> None:
        """Gera em lote os resumos dos documentos pendentes do ticker."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        if getattr(self, "_resumos_job", None) is not None:
            return
        pendentes = painel.documentos_sem_resumo()
        if not pendentes:
            painel.refresh_resumir_button()
            return
        ticker = self._ticker_apresentado()
        job = ResumosPendentesJob(
            painel, pendentes, cancel_token=self._presenter.cancel_token
        )
        self._resumos_job = job
        self._resumos_ticker = ticker
        self._resumos_resumidos = 0
        self._resumos_fase = None
        self._resumos_fase_inicio = None
        self._resumos_fase_completa = False
        self._resumos_interrompido = False
        self._resumos_reporter = ProgressReporter(
            on_update=self._presenter.on_progress
        )
        self._presenter.enter()
        self._presenter.job_cancelavel_iniciado()
        self._set_status(f"Resumindo {len(pendentes)} documento(s)…")
        try:
            job.iniciar()
        except Exception:
            logger.exception("Falha ao iniciar o lote de resumos")
            if getattr(self, "_resumos_job", None) is job:
                self._resumos_job = None
            self._presenter.job_cancelavel_finalizado()
            self._presenter.exit()
            return
        self._poll_resumos_job(job, ticker)

    def _poll_resumos_job(
        self: "ResumosActionsMixin", job: ResumosPendentesJob, ticker: str | None
    ) -> None:
        """Consome o lote uma mensagem por vez, dando tempo ao Tk de repintar."""
        estado = self._processar_mensagem_resumo(job, ticker)
        if estado == "terminou" or self._cancelamento_solicitado():
            self._finalizar_resumos_job(job, ticker)
            return
        atraso = self._atraso_poll_resumos(estado)
        self.after(atraso, lambda: self._poll_resumos_job(job, ticker))

    def _atraso_poll_resumos(self: "ResumosActionsMixin", estado: str) -> int:
        """Calcula o atraso do próximo poll, garantindo a exibição da fase.

        Só retém a drenagem ao término de uma fase (última unidade), para que o
        rótulo seja pintado mesmo quando a fase é instantânea (textos em
        cache). Durante o avanço da fase, drena sem atraso para que cada
        unidade preparada seja refletida na barra; com a fila momentaneamente
        vazia, aguarda um curto intervalo.
        """
        if estado == "vazio":
            return 50
        if not getattr(self, "_resumos_fase_completa", False):
            return 0
        inicio = getattr(self, "_resumos_fase_inicio", None)
        if inicio is None:
            return 0
        restante = _FASE_RESUMOS_MINIMA_S - (time.monotonic() - inicio)
        return int(restante * 1000) if restante > 0 else 0

    def _processar_mensagem_resumo(
        self: "ResumosActionsMixin", job: ResumosPendentesJob, ticker: str | None
    ) -> str:
        """Processa a próxima mensagem da fila do lote.

        Retorna ``"terminou"`` ao receber o término, ``"processou"`` quando
        tratou uma mensagem e ``"vazio"`` quando a fila está momentaneamente
        vazia.
        """
        try:
            mensagem = job.fila.get_nowait()
        except queue.Empty:
            return "vazio"
        if mensagem is True:
            return "terminou"
        self._tratar_mensagem_resumo(mensagem, ticker)
        return "processou"

    def _tratar_mensagem_resumo(
        self: "ResumosActionsMixin", mensagem: tuple, ticker: str | None
    ) -> None:
        """Roteia uma mensagem do lote para o tratamento correspondente."""
        tipo = mensagem[0]
        if tipo == MENSAGEM_PROGRESSO:
            self._tratar_progresso_resumos(mensagem)
        elif tipo == MENSAGEM_RESULTADO:
            self._aplicar_resultado_resumo(mensagem, ticker)
        elif tipo == MENSAGEM_ERRO:
            self._interromper_resumos(mensagem)

    def _tratar_progresso_resumos(
        self: "ResumosActionsMixin", mensagem: tuple
    ) -> None:
        """Traduz o progresso do lote para o relator de fases."""
        _tipo, fase, current, total, label = mensagem
        reporter = getattr(self, "_resumos_reporter", None)
        if reporter is None:
            return
        detalhe = f"{current}/{total}"
        if fase != getattr(self, "_resumos_fase", None):
            self._resumos_fase = fase
            self._resumos_fase_inicio = time.monotonic()
            reporter.start_phase(label, total, weight=1)
            reporter.advance(0, detalhe)
        elif current > 0:
            reporter.advance(1, detalhe)
        self._resumos_fase_completa = total <= 0 or current >= total

    def _aplicar_resultado_resumo(
        self: "ResumosActionsMixin", mensagem: tuple, ticker: str | None
    ) -> None:
        """Aplica um resumo gerado, descartando-o se o ticker mudou."""
        _tipo, arquivo, resumo = mensagem
        if ticker != self._ticker_apresentado():
            return
        painel = getattr(self, "_documents_panel", None)
        if painel is None or resumo is None:
            return
        painel.aplicar_resumo(arquivo, resumo)
        self._resumos_resumidos = getattr(self, "_resumos_resumidos", 0) + 1

    def _interromper_resumos(
        self: "ResumosActionsMixin", mensagem: tuple
    ) -> None:
        """Registra e reporta a interrupção do lote por erro."""
        _tipo, arquivo, exc = mensagem
        self._resumos_interrompido = True
        logger.error(
            "Resumo em lote interrompido em %s: %s",
            arquivo.caminho,
            exc,
            exc_info=exc,
        )
        self._set_status(f"{arquivo.nome}: {mensagem_erro_llm(exc)}", "⚠")

    def _finalizar_resumos_job(
        self: "ResumosActionsMixin", job: ResumosPendentesJob, ticker: str | None
    ) -> None:
        """Encerra o lote, libera o estado ocupado e exibe o desfecho."""
        if getattr(self, "_resumos_job", None) is job:
            self._resumos_job = None
        if self._cancelamento_solicitado():
            self._resumos_interrompido = True
        self._presenter.job_cancelavel_finalizado()
        self._presenter.exit()
        painel = getattr(self, "_documents_panel", None)
        if painel is not None:
            painel.refresh_resumir_button()
        if getattr(self, "_resumos_interrompido", False):
            return
        if ticker != self._ticker_apresentado():
            return
        total = getattr(job, "total", 0)
        sem_texto = getattr(job, "sem_texto", 0)
        resumidos = getattr(self, "_resumos_resumidos", 0)
        self._flash_status(
            f"Resumos gerados: {resumidos} de {total} ({sem_texto} sem texto).",
            "✓",
        )
