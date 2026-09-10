"""Controlador da interface gráfica do FlowScope."""

import queue
from collections.abc import Callable
from datetime import date, datetime, timezone

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.application.load_portfolio_use_case import (
    LoadIndexPortfolioUseCase,
    PortfolioNotFoundError,
)
from flowscope.application.logging_port import LogEntry, LogPort
from flowscope.application.operation_guard import OperationGuard
from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.infrastructure.fii.b3_price import B3MarketPriceFromResult
from flowscope.presentation.gui.fundamental_job import (
    MENSAGEM_ERRO,
    MENSAGEM_PROGRESSO,
    MENSAGEM_RESULTADO,
    FundamentalJob,
)
from flowscope.presentation.gui.presenter import FlowScopePresenter
from flowscope.presentation.gui.progress import ProgressReporter


class FlowScopeController:
    """Controlador que orquestra as operações de carga e análise de dados."""

    def __init__(
        self: "FlowScopeController",
        guard: OperationGuard,
        load_portfolio: LoadIndexPortfolioUseCase,
        analyze: AnalyzeTickersUseCase,
        presenter: FlowScopePresenter,
        logger: LogPort,
        fundamental_repo: object | None = None,
        fundamental_provider: object | None = None,
        fundamental_ffo_provider: object | None = None,
    ) -> None:
        """Inicializa o controlador com as dependências da aplicação."""
        self._guard = guard
        self._load_portfolio = load_portfolio
        self._analyze = analyze
        self._presenter = presenter
        self._logger = logger
        self._fundamental_repo = fundamental_repo
        self._fundamental_provider = fundamental_provider
        self._fundamental_ffo_provider = fundamental_ffo_provider
        self._fundamental_generation = 0
        self._fundamental_job: FundamentalJob | None = None

    def _make_progress_cb(
        self: "FlowScopeController", reporter: ProgressReporter,
    ) -> Callable[[str, bool], None]:
        def _cb(detail: str, failed: bool) -> None:
            if failed:
                reporter.fail(1, detail)
            else:
                reporter.advance(1, detail)
        return _cb

    def _iniciar_analise_fundamental(
        self: "FlowScopeController",
        tickers: list[str],
        ref_date: date,
        result: dict,
    ) -> None:
        """Dispara a análise fundamentalista em background, se configurada."""
        if self._fundamental_repo is None:
            return
        daily = {
            ticker: dados.get("daily_data", [])
            for ticker, dados in result.items()
            if isinstance(dados, dict)
        }
        self._fundamental_generation += 1
        caso = FundamentalAnalysisUseCase(
            repository=self._fundamental_repo,
            mercado=B3MarketPriceFromResult(daily),
            fundamental_provider=self._fundamental_provider,
            ffo_provider=self._fundamental_ffo_provider,
        )
        job = FundamentalJob(
            caso, tickers, ref_date, self._fundamental_generation
        )
        self._fundamental_job = job
        self._presenter.on_fundamental_started()
        job.iniciar()
        self._drenar_fundamental(job)

    def _drenar_fundamental(
        self: "FlowScopeController", job: FundamentalJob | None = None
    ) -> None:
        """Consome a fila do job na thread do Tk e agenda a próxima leitura."""
        job = job or self._fundamental_job
        if job is None or job is not self._fundamental_job:
            return
        terminou = False
        try:
            while True:
                mensagem = job.fila.get_nowait()
                tipo = mensagem[0]
                if tipo == MENSAGEM_PROGRESSO:
                    self._presenter.on_fundamental_progress(mensagem[1])
                elif tipo == MENSAGEM_RESULTADO:
                    if job.generation == self._fundamental_generation:
                        houve_falha = mensagem[2] if len(mensagem) > 2 else False
                        self._presenter.on_fundamental_result(
                            mensagem[1], houve_falha
                        )
                    terminou = True
                elif tipo == MENSAGEM_ERRO:
                    if job.generation == self._fundamental_generation:
                        self._presenter.on_fundamental_error()
                    terminou = True
        except queue.Empty:
            pass
        if terminou:
            if job is self._fundamental_job:
                self._fundamental_job = None
            self._presenter.on_fundamental_finished()
            return
        self._presenter.agendar(100, lambda: self._drenar_fundamental(job))

    def on_index_clicked(self: "FlowScopeController", index: str) -> None:
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

    def on_load_data(self: "FlowScopeController", ref_date: date | None = None) -> None:
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

    def on_today(self: "FlowScopeController") -> None:
        """Carrega os dados para a data atual."""
        self._presenter._gui._date_entry.set_date(datetime.now(timezone.utc).date())
        self.on_load_data()

    def on_ticker_edit(self: "FlowScopeController") -> None:
        """Atualiza a análise ao editar a lista de tickers."""
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
