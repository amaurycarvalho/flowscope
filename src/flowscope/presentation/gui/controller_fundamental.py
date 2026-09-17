"""Mixin de análise fundamentalista em background do controlador."""

import queue
import time
from datetime import date

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.logging_port import LogEntry
from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult
from flowscope.presentation.gui.fundamental_job import (
    MENSAGEM_ERRO,
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    FundamentalJob,
)

#: Tempo máximo sem progresso antes de encerrar a análise por inatividade.
_LIMITE_INATIVIDADE_S = 120.0


class FundamentalMixin:
    """Mixin que dispara e drena a análise fundamentalista em background."""

    def _iniciar_analise_fundamental(
        self: "FundamentalMixin",
        tickers: list[str],
        ref_date: date,
        result: dict,
        force: bool = False,
    ) -> None:
        """Dispara a análise fundamentalista em background, se configurada."""
        if self._fundamental_repo is None:
            return
        daily = {
            ticker: dados.get("daily_data", [])
            for ticker, dados in result.items()
            if isinstance(dados, dict)
        }
        job_anterior = self._fundamental_job
        self._fundamental_generation += 1
        caso = FundamentalAnalysisUseCase(
            repository=self._fundamental_repo,
            mercado=B3MarketPriceFromResult(daily),
            fundamental_provider=self._fundamental_provider,
            ffo_provider=self._fundamental_ffo_provider,
            historico_dividendos=self._fundamental_dividend_provider,
            acionistas_provider=self._fundamental_acionistas_provider,
            indexadores_provider=self._fundamental_indexadores_provider,
            historico_store=self._fundamental_history_store,
            resolver_fiagro=self._fundamental_resolver_fiagro,
            bdr_provider=self._fundamental_bdr_provider,
        )
        job = FundamentalJob(
            caso, tickers, ref_date, self._fundamental_generation,
            force_refresh=force,
        )
        self._fundamental_job = job
        self._fundamental_ultima_atividade = time.monotonic()
        self._presenter.on_fundamental_started()
        if job_anterior is not None:
            self._presenter.on_fundamental_finished()
        self._presenter.on_progress(0, len(tickers), "• Fundamentos...")
        job.iniciar()
        self._drenar_fundamental(job)

    def on_atualizar_fundamentos(self: "FundamentalMixin") -> None:
        """Força a recomputação dos fundamentos da data, ignorando o cache."""
        if self._fundamental_repo is None:
            return
        if self._fundamental_job is not None:
            return
        tickers = self._presenter.get_current_tickers()
        if not tickers:
            return
        ref_date = self._presenter.get_reference_date()
        current = getattr(self._presenter._gui, "_current_data", {}) or {}
        self._iniciar_analise_fundamental(tickers, ref_date, current, force=True)

    def _drenar_fundamental(
        self: "FundamentalMixin", job: FundamentalJob | None = None
    ) -> None:
        """Consome a fila do job na thread do Tk e agenda a próxima leitura."""
        job = job or self._fundamental_job
        if job is None or job is not self._fundamental_job:
            return
        try:
            terminou = self._consumir_fila(job)
        except Exception as e:
            self._logger.error(LogEntry(
                message=str(e),
                level="ERROR",
                component="Controller._drenar_fundamental",
                exception=e,
            ))
            terminou = True
        if not terminou and self._job_travado(job):
            self._logger.warning(LogEntry(
                message=(
                    "Análise fundamentalista sem progresso; encerrando para "
                    "restaurar a interface."
                ),
                level="WARNING",
                component="Controller._drenar_fundamental",
                context={"generation": getattr(job, "generation", "")},
            ))
            terminou = True
        if terminou:
            if job is self._fundamental_job:
                self._fundamental_job = None
            self._presenter.on_fundamental_finished()
            return
        self._presenter.agendar(100, lambda: self._drenar_fundamental(job))

    def _job_travado(self: "FundamentalMixin", job: FundamentalJob) -> bool:
        """Indica se o job morreu ou ficou sem progresso por tempo demais."""
        thread = getattr(job, "thread", None)
        if thread is not None and not thread.is_alive() and job.fila.empty():
            return True
        ultima = getattr(self, "_fundamental_ultima_atividade", None)
        if ultima is None:
            return False
        return time.monotonic() - ultima > _LIMITE_INATIVIDADE_S

    def _consumir_fila(self: "FundamentalMixin", job: FundamentalJob) -> bool:
        """Esvazia a fila do job e informa se ele foi concluído.

        Uma falha ao tratar uma mensagem (ex.: erro de renderização de um
        painel) é registrada no log e não interrompe o esvaziamento da fila.
        Mensagens terminais tratadas com falha ainda encerram o job, de modo
        que o cursor e os controles sempre sejam restaurados.
        """
        terminou = False
        try:
            while True:
                mensagem = job.fila.get_nowait()
                try:
                    terminou = self._tratar_mensagem(job, mensagem) or terminou
                except Exception as e:
                    self._logger.error(LogEntry(
                        message=str(e),
                        level="ERROR",
                        component="Controller._consumir_fila",
                        exception=e,
                        context={"tipo_mensagem": str(mensagem[0])},
                    ))
                    terminou = terminou or mensagem[0] in (
                        MENSAGEM_RESULTADO, MENSAGEM_ERRO
                    )
        except queue.Empty:
            pass
        return terminou

    def _tratar_mensagem(
        self: "FundamentalMixin", job: FundamentalJob, mensagem: tuple
    ) -> bool:
        """Trata uma mensagem do job, retornando se ele foi concluído."""
        tipo = mensagem[0]
        if tipo == MENSAGEM_PROGRESSO:
            self._tratar_progresso(mensagem)
            return False
        if tipo == MENSAGEM_RESULTADO:
            if job.generation == self._fundamental_generation:
                houve_falha = mensagem[2] if len(mensagem) > 2 else False
                self._presenter.on_fundamental_result(mensagem[1], houve_falha)
            return True
        if tipo == MENSAGEM_ERRO:
            if job.generation == self._fundamental_generation:
                self._presenter.on_fundamental_error()
            return True
        return False

    def _tratar_progresso(self: "FundamentalMixin", mensagem: tuple) -> None:
        """Repassa uma mensagem de progresso ao presenter."""
        self._fundamental_ultima_atividade = time.monotonic()
        detalhe = mensagem[1]
        if len(mensagem) >= 5:
            self._presenter.on_fundamental_progress(
                detalhe, mensagem[3], mensagem[4]
            )
        else:
            self._presenter.on_fundamental_progress(detalhe)
