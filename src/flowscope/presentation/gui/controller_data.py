"""Mixins de carga de dados e análise fundamentalista do controlador."""

from collections.abc import Callable
from datetime import date

from flowscope.application.load_portfolio_use_case import (
    PortfolioNotFoundError,
)
from flowscope.application.logging_port import LogEntry
from flowscope.presentation.gui.progress import ProgressReporter


class DataLoadMixin:
    """Mixin com as operações de carga de portfólio e dados históricos."""

    def _make_progress_cb(
        self: "DataLoadMixin", reporter: ProgressReporter,
    ) -> Callable[[str, bool], None]:
        def _cb(detail: str, failed: bool) -> None:
            if failed:
                reporter.fail(1, detail)
            else:
                reporter.advance(1, detail)
        return _cb

    def on_index_clicked(self: "DataLoadMixin", index: str) -> None:
        """Carrega o portfólio e os dados históricos do índice selecionado."""
        with self._guard.acquire() as ok:
            if not ok:
                return
            self._presenter.on_operation_started()
            reporter = ProgressReporter(
                on_update=self._presenter.on_progress,
            )

            try:
                reporter.start_phase(
                    f"Baixando portfólio {index}...", total=1, weight=1,
                )

                tickers = self._load_portfolio.execute(
                    index,
                    progress_callback=self._make_progress_cb(reporter),
                )
                reporter.finish_phase()

                self._presenter.on_portfolio_loaded(tickers)

                ref_date = self._presenter.get_reference_date()
                config = self._presenter.get_sampling_config()
                reporter.start_phase(
                    "Baixando dados históricos", total=7, weight=3,
                )

                result = self._analyze.execute(
                    ref_date, tickers,
                    progress_callback=self._make_progress_cb(reporter),
                    config=config,
                )
                reporter.finish_phase()

                reporter.start_phase(
                    "Processando indicadores", total=1, weight=2,
                )
                reporter.finish_phase()

                self._presenter.on_result(result, tickers, ref_date)
                self._iniciar_analise_fundamental(tickers, ref_date, result)

            except PortfolioNotFoundError:
                self._presenter.set_status(
                    f"Não foi possível carregar a carteira {index}.", "⚠",
                )
            except Exception as e:
                ref = self._logger.error(LogEntry(
                    message=str(e),
                    level="ERROR",
                    component="Controller.on_index_clicked",
                    exception=e,
                    context={"index": index},
                ))
                self._presenter.on_technical_error(e, ref)
            finally:
                self._presenter.on_operation_finished()

    def on_load_data(self: "DataLoadMixin", ref_date: date | None = None) -> None:
        """Carrega os dados dos tickers atuais, carregando a carteira se vazia."""
        with self._guard.acquire() as ok:
            if not ok:
                return
            self._presenter.on_operation_started()
            reporter = ProgressReporter(
                on_update=self._presenter.on_progress,
            )

            try:
                tickers = self._presenter.get_current_tickers()
                if not tickers:
                    reporter.start_phase(
                        "Carregando IDIV...", total=1, weight=1,
                    )
                    tickers = self._load_portfolio.execute(
                        "IDIV",
                        progress_callback=self._make_progress_cb(reporter),
                    )
                    reporter.finish_phase()
                    self._presenter.on_portfolio_loaded(tickers)

                if ref_date is None:
                    ref_date = self._presenter.get_reference_date()

                config = self._presenter.get_sampling_config()
                reporter.start_phase(
                    "Baixando dados históricos", total=7, weight=3,
                )

                result = self._analyze.execute(
                    ref_date, tickers,
                    progress_callback=self._make_progress_cb(reporter),
                    config=config,
                )
                reporter.finish_phase()

                reporter.start_phase(
                    "Processando indicadores", total=1, weight=2,
                )
                reporter.finish_phase()

                self._presenter.on_result(result, tickers, ref_date)
                self._iniciar_analise_fundamental(tickers, ref_date, result)

            except PortfolioNotFoundError:
                self._presenter.set_status(
                    "Filtro vazio e não foi possível carregar a carteira IDIV.",
                    "⚠",
                )
            except Exception as e:
                ref = self._logger.error(LogEntry(
                    message=str(e),
                    level="ERROR",
                    component="Controller.on_load_data",
                    exception=e,
                    context={"ref_date": str(ref_date)},
                ))
                self._presenter.on_technical_error(e, ref)
            finally:
                self._presenter.on_operation_finished()
