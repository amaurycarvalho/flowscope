from datetime import date

from flowscope.application.load_portfolio_use_case import (
    LoadIndexPortfolioUseCase,
    PortfolioNotFoundError,
)
from flowscope.application.logging_port import LogEntry, LogPort
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.presentation.gui.presenter import FlowScopePresenter
from flowscope.presentation.gui.progress import ProgressReporter


class FlowScopeController:
    def __init__(
        self,
        guard: OperationGuard,
        load_portfolio: LoadIndexPortfolioUseCase,
        analyze: AnalyzeTickersUseCase,
        presenter: FlowScopePresenter,
        logger: LogPort,
    ):
        self._guard = guard
        self._load_portfolio = load_portfolio
        self._analyze = analyze
        self._presenter = presenter
        self._logger = logger

    def _make_progress_cb(self, reporter: ProgressReporter):
        def _cb(detail: str, failed: bool) -> None:
            if failed:
                reporter.fail(1, detail)
            else:
                reporter.advance(1, detail)
        return _cb

    def on_index_clicked(self, index: str) -> None:
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
                reporter.start_phase(
                    "Baixando dados históricos", total=7, weight=3,
                )

                result = self._analyze.execute(
                    ref_date, tickers,
                    progress_callback=self._make_progress_cb(reporter),
                )
                reporter.finish_phase()

                reporter.start_phase(
                    "Processando indicadores", total=1, weight=2,
                )
                reporter.finish_phase()

                self._presenter.on_result(result, tickers, ref_date)

            except PortfolioNotFoundError:
                self._presenter.on_operation_finished()
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

    def on_load_data(self, ref_date: date | None = None) -> None:
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

                reporter.start_phase(
                    "Baixando dados históricos", total=7, weight=3,
                )

                result = self._analyze.execute(
                    ref_date, tickers,
                    progress_callback=self._make_progress_cb(reporter),
                )
                reporter.finish_phase()

                reporter.start_phase(
                    "Processando indicadores", total=1, weight=2,
                )
                reporter.finish_phase()

                self._presenter.on_result(result, tickers, ref_date)

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

    def on_today(self) -> None:
        self._presenter._gui._date_entry.set_date(date.today())
        self.on_load_data()

    def on_ticker_edit(self) -> None:
        tickers = self._presenter.get_current_tickers()
        if not tickers:
            try:
                tickers = self._load_portfolio.execute("IDIV")
            except PortfolioNotFoundError:
                self._presenter._gui._flash_status(
                    "Não foi possível carregar a carteira IDIV.", "⚠",
                )
                return
            self._presenter.on_portfolio_loaded(tickers)
        self._presenter._gui._tickers = list(tickers)
        self._presenter._gui._set_wait_cursor()
        try:
            current = self._presenter._gui._resolve_current_chart()
            if current and self._presenter._gui._current_data:
                self._presenter._gui._do_update(current)
        finally:
            self._presenter._gui._clear_wait_cursor()
        self._presenter._gui._flash_status("Filtro aplicado!", "ℹ")
