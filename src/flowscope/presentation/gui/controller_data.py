"""Mixins de carga de dados e análise fundamentalista do controlador.

A carga principal deixa de rodar de forma síncrona na thread do Tk: o
controlador monta uma :class:`InstrucaoCarga` (lendo a data e a amostragem da
view) e submete o trabalho ao gerenciador de background, no grupo ``carga``.
O :class:`ProgressReporter` e o processamento ficam no worker; o resultado é
entregue por evento e a renderização ocorre na thread do Tk.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from flowscope.application.cancellation import OperacaoCancelada
from flowscope.application.load_portfolio_use_case import (
    PortfolioNotFoundError,
)
from flowscope.application.logging_port import LogEntry
from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import (
    Erro,
    Progresso,
    Resultado,
)
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.progress import ProgressReporter

#: Grupo e política da carga principal no gerenciador de background.
GRUPO_CARGA = "carga"
POLITICA_CARGA = Politica.LATEST_WINS

#: Origens possíveis de uma carga principal.
ORIGEM_INDEX = "index"
ORIGEM_LOAD = "load"
ORIGEM_PORTFOLIO = "portfolio"


@dataclass(frozen=True)
class InstrucaoCarga:
    """Descreve uma carga principal a ser executada em background."""

    origem: str
    index: str | None
    tickers: list[str]
    ref_date: date
    config: SamplingConfig
    componente: str

    @property
    def chave(self: "InstrucaoCarga") -> tuple[object, ...]:
        """Chave de deduplicação: índice (ou origem), data e amostragem."""
        alvo: object = self.index if self.index else self.origem
        return (alvo, self.ref_date, self.config.period_days, self.config.method)


@dataclass(frozen=True)
class ResultadoCarga:
    """Resultado final de uma carga principal entregue por evento."""

    origem: str
    result: dict | None
    tickers: list[str]
    ref_date: date
    portfolio_carregado: bool


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
        """Submete a carga do portfólio e dos dados históricos do índice."""
        self._submeter_carga(
            self._montar_instrucao(ORIGEM_INDEX, index, [], None)
        )

    def on_load_data(self: "DataLoadMixin", ref_date: date | None = None) -> None:
        """Submete a carga dos dados dos tickers atuais (ou da carteira IDIV)."""
        tickers = self._presenter.get_current_tickers()
        index = None if tickers else "IDIV"
        self._submeter_carga(
            self._montar_instrucao(ORIGEM_LOAD, index, tickers, ref_date)
        )

    def _montar_instrucao(
        self: "DataLoadMixin",
        origem: str,
        index: str | None,
        tickers: list[str],
        ref_date: date | None,
    ) -> InstrucaoCarga:
        """Captura os dados de configuração da view para a carga em background."""
        if ref_date is None:
            ref_date = self._presenter.get_reference_date()
        config = self._presenter.get_sampling_config()
        return InstrucaoCarga(
            origem=origem,
            index=index,
            tickers=list(tickers),
            ref_date=ref_date,
            config=config,
            componente=_componente_log(origem),
        )

    def _submeter_carga(
        self: "DataLoadMixin", instrucao: InstrucaoCarga, usar_guard: bool = True,
    ) -> None:
        """Submete a carga ao manager, opcionalmente sob a guarda síncrona."""
        if self._background is None:
            return
        if not usar_guard:
            self._enviar_carga(instrucao)
            return
        with self._guard.acquire() as ok:
            if not ok:
                return
            self._enviar_carga(instrucao)

    def _enviar_carga(self: "DataLoadMixin", instrucao: InstrucaoCarga) -> None:
        """Envia o trabalho de carga ao gerenciador de background."""
        self._background.submit(
            lambda ctx: self._trabalho_carga(ctx, instrucao),
            grupo=GRUPO_CARGA,
            politica=POLITICA_CARGA,
            chave=instrucao.chave,
            cancelavel=True,
            ao_progresso=self._ao_progresso_carga,
            ao_resultado=self._ao_resultado_carga,
            ao_erro=self._ao_erro_carga,
        )

    def _trabalho_carga(
        self: "DataLoadMixin", ctx: JobContext, instrucao: InstrucaoCarga,
    ) -> None:
        """Executa a carga no worker, publicando progresso e o resultado.

        O :class:`ProgressReporter` é criado e avançado aqui, fora da thread do
        Tk. Ao detectar cancelamento, o resultado parcial é descartado e nada é
        publicado.
        """
        reporter = ProgressReporter(
            on_update=lambda current, total, label: ctx.progress(
                detalhe=label, atual=current, total=total,
            ),
        )
        progress_cb = self._make_progress_cb(reporter)
        tickers = list(instrucao.tickers)
        portfolio_carregado = False

        try:
            if not tickers:
                reporter.start_phase(
                    _rotulo_portfolio(instrucao), total=1, weight=1,
                )
                tickers = self._load_portfolio.execute(
                    instrucao.index,
                    progress_callback=progress_cb,
                    cancel_token=ctx.token,
                )
                reporter.finish_phase()
                portfolio_carregado = True

            if instrucao.origem == ORIGEM_PORTFOLIO:
                ctx.raise_if_cancelled()
                ctx.resultado(valor=ResultadoCarga(
                    origem=instrucao.origem,
                    result=None,
                    tickers=tickers,
                    ref_date=instrucao.ref_date,
                    portfolio_carregado=True,
                ))
                return

            reporter.start_phase(
                "Baixando dados históricos", total=7, weight=3,
            )
            result = self._analyze.execute(
                instrucao.ref_date, tickers,
                progress_callback=progress_cb,
                config=instrucao.config,
                cancel_token=ctx.token,
            )
            reporter.finish_phase()

            reporter.start_phase(
                "Processando indicadores", total=1, weight=2,
            )
            reporter.finish_phase()
            ctx.raise_if_cancelled()
        except OperacaoCancelada:
            return
        except PortfolioNotFoundError as exc:
            ctx.falhar(exc, dados=instrucao)
            return
        except Exception as exc:
            ctx.falhar(exc, dados=instrucao)
            return

        ctx.resultado(valor=ResultadoCarga(
            origem=instrucao.origem,
            result=result,
            tickers=tickers,
            ref_date=instrucao.ref_date,
            portfolio_carregado=portfolio_carregado,
        ))

    def _ao_progresso_carga(
        self: "DataLoadMixin", evento: Progresso,
    ) -> None:
        """Repassa o progresso do job de carga ao presenter."""
        self._presenter.on_progress(evento.atual, evento.total, evento.detalhe)

    def _ao_resultado_carga(
        self: "DataLoadMixin", evento: Resultado,
    ) -> None:
        """Aplica o resultado da carga na thread do Tk."""
        resultado = evento.valor
        if resultado.origem == ORIGEM_PORTFOLIO:
            self._aplicar_carteira(resultado.tickers, anunciar=True)
            self._presenter._gui._flash_status("Filtro aplicado!", "ℹ")
            return
        if resultado.portfolio_carregado:
            self._presenter.on_portfolio_loaded(resultado.tickers)
        self._presenter.on_result(
            resultado.result, resultado.tickers, resultado.ref_date,
        )
        self._iniciar_analise_fundamental(
            resultado.tickers, resultado.ref_date, resultado.result,
        )

    def _ao_erro_carga(self: "DataLoadMixin", evento: Erro) -> None:
        """Reporta a falha da carga com a mensagem correspondente à origem."""
        instrucao = evento.dados
        if isinstance(evento.excecao, PortfolioNotFoundError):
            self._reportar_portfolio_ausente(instrucao)
            return
        componente = instrucao.componente if instrucao else "Controller.on_load_data"
        ref = self._logger.error(LogEntry(
            message=str(evento.excecao),
            level="ERROR",
            component=componente,
            exception=evento.excecao,
            context=_contexto_log(instrucao),
        ))
        self._presenter.on_technical_error(evento.excecao, ref)

    def _reportar_portfolio_ausente(self: "DataLoadMixin", instrucao: object) -> None:
        """Exibe a mensagem de portfólio ausente conforme a origem da carga."""
        origem = getattr(instrucao, "origem", ORIGEM_LOAD)
        if origem == ORIGEM_PORTFOLIO:
            self._presenter._gui._flash_status(
                "Não foi possível carregar a carteira IDIV.", "⚠",
            )
            return
        if origem == ORIGEM_LOAD:
            self._presenter.set_status(
                "Filtro vazio e não foi possível carregar a carteira IDIV.",
                "⚠",
            )
            return
        index = getattr(instrucao, "index", None)
        self._presenter.set_status(
            f"Não foi possível carregar a carteira {index}.", "⚠",
        )

    def _aplicar_carteira(
        self: "DataLoadMixin", tickers: list[str], anunciar: bool,
    ) -> None:
        """Aplica a carteira na view e atualiza o gráfico corrente."""
        if anunciar:
            self._presenter.on_portfolio_loaded(tickers)
        self._presenter._gui._tickers = list(tickers)
        with self._presenter.busy():
            current = self._presenter._gui._resolve_current_chart()
            if current and self._presenter._gui._deve_atualizar(current):
                self._presenter._gui._do_update(current)


def _rotulo_portfolio(instrucao: InstrucaoCarga) -> str:
    """Retorna o rótulo da fase inicial de download da carteira."""
    if instrucao.origem == ORIGEM_INDEX:
        return f"Baixando portfólio {instrucao.index}..."
    return "Carregando IDIV..."


def _componente_log(origem: str) -> str:
    """Retorna o componente de log associado à origem da carga."""
    if origem == ORIGEM_INDEX:
        return "Controller.on_index_clicked"
    if origem == ORIGEM_PORTFOLIO:
        return "Controller.on_ticker_edit"
    return "Controller.on_load_data"


def _contexto_log(instrucao: object) -> dict:
    """Retorna o contexto de log da carga."""
    if instrucao is not None and getattr(instrucao, "origem", None) == ORIGEM_INDEX:
        return {"index": instrucao.index}
    ref_date = getattr(instrucao, "ref_date", None)
    return {"ref_date": str(ref_date)}
