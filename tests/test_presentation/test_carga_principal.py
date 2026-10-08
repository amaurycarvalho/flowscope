"""Testes headless da carga principal em background.

Exercitam a submissão ao grupo ``carga``, a deduplicação por ``key``, o
supersede, o repasse de token de cancelamento e o descarte do resultado por
evento, usando um presenter fake e o ``BackgroundManager`` real, sem ``tk.Tk``.
"""

import threading
import time
from datetime import date
from unittest.mock import MagicMock

from flowscope.application.operation_guard import OperationGuard
from flowscope.domain.sampling import SamplingConfig
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Progresso, Resultado
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.controller_data import InstrucaoCarga
from flowscope.presentation.gui.presenter import FlowScopePresenter

REFERENCIA = date(2026, 9, 4)
CONFIG = SamplingConfig(period_days=30, method="fibonacci")


class _ViewFake:
    """View mínima que registra o estado observável usado pelo presenter."""

    def __init__(self) -> None:
        self.cancellable = False
        self.progress_visible = False
        self.status: tuple[str, str] | None = None
        self.cursor_busy = False
        self.buttons_disabled = False
        self.tickers: list[str] = []
        self.current_tickers: list[str] = []
        self.ref_date = REFERENCIA
        self.config = CONFIG
        self.current_data: dict = {}
        self.tickers_list: list[str] = []
        self.flash: list[tuple[str, str]] = []
        self.chart = None
        self.restaurado = 0
        self.progress: tuple[int, int, str] | None = None
        self.progress_updates = 0

    def set_cancellable(self, value: bool) -> None:
        self.cancellable = value

    def set_progress(self, current: int, total: int, label: str) -> None:
        self.progress_visible = True
        self.progress = (current, total, label)
        self.progress_updates += 1

    def clear_progress(self) -> None:
        self.progress_visible = False

    def disable_all_buttons(self) -> None:
        self.buttons_disabled = True

    def restore_all_buttons(self) -> None:
        self.buttons_disabled = False
        self.restaurado += 1

    def enter_busy(self) -> None:
        self.cursor_busy = True

    def exit_busy(self) -> None:
        self.cursor_busy = False

    def set_status(self, msg: str, icon: str = "") -> None:
        self.status = (msg, icon)

    def set_tickers(self, tickers: list[str]) -> None:
        self.tickers = list(tickers)

    def set_current_data(self, data: dict) -> None:
        self.current_data = data

    def set_tickers_list(self, tickers: list[str]) -> None:
        self.tickers_list = list(tickers)

    def set_counter(self, text: str) -> None:
        pass

    def set_date_label(self, text: str) -> None:
        pass

    def on_tab_changed(self) -> None:
        pass

    def config_copy_button_state(self, state: str) -> None:
        pass

    def get_reference_date(self) -> date:
        return self.ref_date

    def get_current_tickers(self) -> list[str]:
        return list(self.current_tickers)

    def get_sampling_config(self) -> SamplingConfig:
        return self.config

    def set_fundamental_data(self, dados: dict) -> None:
        pass

    def _flash_status(self, msg: str, icon: str = "", clear_ms: int = 2500) -> None:
        self.flash.append((msg, icon))

    def _resolve_current_chart(self) -> object | None:
        return self.chart

    def _deve_atualizar(self, chart: object) -> bool:
        return True

    def _do_update(self, chart: object) -> None:
        chart.updated = True


def _montar(controller_kwargs: dict | None = None):
    view = _ViewFake()
    presenter = FlowScopePresenter(view)
    load_portfolio = MagicMock()
    load_portfolio.execute.return_value = ["PETR4", "VALE3"]
    analyze = MagicMock()
    analyze.execute.return_value = {"PETR4": {"daily_data": []}}
    background = BackgroundManager()
    background.ao_iniciar(lambda handle: presenter.on_operation_started())
    background.ao_terminar(
        lambda handle: presenter.exit(handle.outcome, handle.falha_reportada)
    )
    presenter.attach_background(background)
    controller = FlowScopeController(
        guard=OperationGuard(),
        load_portfolio=load_portfolio,
        analyze=analyze,
        presenter=presenter,
        logger=MagicMock(),
        background=background,
        **(controller_kwargs or {}),
    )
    return controller, presenter, view, background, load_portfolio, analyze


def _concluir(background: BackgroundManager) -> None:
    """Aguarda as threads ativas e drena os eventos na thread corrente."""
    for handle in list(background.jobs_ativos):
        if handle.thread is not None:
            handle.thread.join(2)
    background.drenar()


def _espionar(objeto: object, nomes: tuple[str, ...], registro: list[str]) -> None:
    """Registra a ordem das chamadas aos métodos informados."""
    for nome in nomes:
        original = getattr(objeto, nome)

        def _fazer(orig=original, chave=nome):
            def _registrar(*args, **kwargs):
                registro.append(chave)
                return orig(*args, **kwargs)

            return _registrar

        setattr(objeto, nome, _fazer())


class TestSubmissaoCarga:
    def test_on_index_clicked_retorna_sem_bloquear(self):
        controller, _, _, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()

        def _execute(*args, **kwargs):
            bloqueio.wait(2)
            return ["PETR4"]

        load_portfolio.execute.side_effect = _execute
        inicio = time.monotonic()
        controller.on_index_clicked("IBOV")
        decorrido = time.monotonic() - inicio
        assert decorrido < 0.5
        assert background.tem_ativo("carga") is True

        bloqueio.set()
        _concluir(background)

    def test_on_index_clicked_usa_chave_derivada(self):
        controller, _, _, background, _, _ = _montar()
        controller.on_index_clicked("IBOV")
        handle = background.jobs_ativos[0]
        assert handle.grupo == "carga"
        assert handle.chave == ("IBOV", REFERENCIA, 30, "fibonacci")
        _concluir(background)

    def test_resultado_passa_pelo_presenter_na_ordem(self):
        controller, presenter, view, background, _, _ = _montar()
        registro: list[str] = []
        _espionar(
            presenter,
            (
                "on_operation_started",
                "on_portfolio_loaded",
                "on_result",
                "exit",
            ),
            registro,
        )

        controller.on_index_clicked("IBOV")
        _concluir(background)

        assert registro == [
            "on_operation_started",
            "on_portfolio_loaded",
            "on_result",
            "exit",
        ]
        assert view.tickers == ["PETR4", "VALE3"]


class TestConcorrencia:
    def test_requisicao_identica_e_descartada(self):
        controller, _, _, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()
        load_portfolio.execute.side_effect = lambda *a, **k: (
            bloqueio.wait(2), ["PETR4"]
        )[1]

        controller.on_index_clicked("IBOV")
        handle1 = background.jobs_ativos[0]
        controller.on_index_clicked("IBOV")

        assert len(background.jobs_ativos) == 1
        assert background.jobs_ativos[0] is handle1
        assert handle1.token.is_set is False

        bloqueio.set()
        _concluir(background)

    def test_carga_distinta_substitui_e_novo_token_limpo(self):
        controller, _, _, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()
        load_portfolio.execute.side_effect = lambda *a, **k: (
            bloqueio.wait(2), ["PETR4"]
        )[1]

        controller.on_index_clicked("IBOV")
        handle1 = background.jobs_ativos[0]
        controller.on_index_clicked("IFIX")

        assert len(background.jobs_ativos) == 1
        handle2 = background.jobs_ativos[0]
        assert handle2 is not handle1
        assert handle1.estado.value == "cancelado"
        assert handle1.token.is_set is True
        assert handle2.token.is_set is False

        bloqueio.set()
        _concluir(background)


class TestCancelamentoCarga:
    def test_resultado_e_descartado_ao_interromper(self):
        controller, presenter, view, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()
        load_portfolio.execute.side_effect = lambda *a, **k: (
            bloqueio.wait(2), ["PETR4"]
        )[1]
        presenter.on_result = MagicMock()

        controller.on_index_clicked("IBOV")
        handle = background.jobs_ativos[0]
        presenter.request_cancel()
        bloqueio.set()
        handle.thread.join(2)
        background.drenar()

        presenter.on_result.assert_not_called()
        assert view.status == ("Processamento interrompido.", "⚠")
        assert view.cancellable is False
        assert view.cursor_busy is False
        assert view.buttons_disabled is False
        assert view.progress_visible is False

    def test_token_repassado_ao_caso_de_uso(self):
        controller, _, _, background, _, analyze = _montar()
        controller.on_index_clicked("IBOV")
        _concluir(background)
        assert analyze.execute.call_args.kwargs["cancel_token"] is not None


class TestSupersedeEstadoOcupado:
    def test_substituicao_nao_restaura_controles(self):
        controller, presenter, view, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()
        load_portfolio.execute.side_effect = lambda *a, **k: (
            bloqueio.wait(2), ["PETR4"]
        )[1]

        controller.on_index_clicked("IBOV")
        assert presenter._operacoes_ativas == 1
        controller.on_index_clicked("IFIX")
        assert presenter._operacoes_ativas == 1

        assert view.restaurado == 0
        assert view.cursor_busy is True

        bloqueio.set()
        for handle in list(background.jobs_ativos):
            handle.thread.join(2)
        background.drenar()

    def test_guard_ocupado_bloqueia_submissao(self):
        controller, _, _, background, _, _ = _montar()
        from contextlib import contextmanager

        @contextmanager
        def _ocupado():
            yield False

        controller._guard.acquire = _ocupado

        controller.on_index_clicked("IBOV")

        assert background.jobs_ativos == ()

    def test_guard_nao_bloqueia_supersede(self):
        controller, _, _, background, load_portfolio, _ = _montar()
        bloqueio = threading.Event()
        load_portfolio.execute.side_effect = lambda *a, **k: (
            bloqueio.wait(2), ["PETR4"]
        )[1]

        controller.on_index_clicked("IBOV")
        controller.on_index_clicked("IFIX")

        assert len(background.jobs_ativos) == 1
        assert controller._guard.is_busy is False

        bloqueio.set()
        _concluir(background)


def _contexto() -> tuple[JobContext, list, JobHandle]:
    handle = JobHandle(id=1, grupo="carga", politica=Politica.LATEST_WINS)
    eventos: list = []
    return JobContext(handle, eventos.append), eventos, handle


def _instrucao_index(index: str = "IBOV") -> InstrucaoCarga:
    return InstrucaoCarga(
        origem="index",
        index=index,
        tickers=[],
        ref_date=REFERENCIA,
        config=CONFIG,
        componente="Controller.on_index_clicked",
    )


class TestTrabalhoCargaWorker:
    def test_fases_do_progresso_criadas_no_worker(self):
        controller, _, _, _, _, _ = _montar()
        ctx, eventos, _ = _contexto()

        controller._trabalho_carga(ctx, _instrucao_index())

        labels = [e.detalhe for e in eventos if isinstance(e, Progresso)]
        assert "Baixando portfólio IBOV..." in labels
        assert "Baixando dados históricos" in labels
        assert "Processando indicadores" in labels
        resultados = [e for e in eventos if isinstance(e, Resultado)]
        assert len(resultados) == 1
        assert resultados[0].valor.tickers == ["PETR4", "VALE3"]

    def test_cancelamento_descarta_resultado_parcial(self):
        controller, _, _, _, _, _ = _montar()
        ctx, eventos, handle = _contexto()
        handle.token.request()

        controller._trabalho_carga(ctx, _instrucao_index())

        assert not any(isinstance(e, Resultado) for e in eventos)


class TestOnLoadData:
    def test_com_tickers_existentes_nao_baixa_carteira(self):
        controller, _, view, background, load_portfolio, analyze = _montar()
        view.current_tickers = ["PETR4"]
        controller.on_load_data()
        _concluir(background)

        load_portfolio.execute.assert_not_called()
        analyze.execute.assert_called_once()
        assert analyze.execute.call_args.args[1] == ["PETR4"]

    def test_sem_tickers_faz_fallback_idiv(self):
        controller, _, view, background, load_portfolio, _ = _montar()
        view.current_tickers = []
        controller.on_load_data()
        _concluir(background)

        args = load_portfolio.execute.call_args.args
        assert args[0] == "IDIV"
        assert view.tickers == ["PETR4", "VALE3"]

    def test_fallback_idiv_ausente_exibe_mensagem(self):
        from flowscope.application.load_portfolio_use_case import (
            PortfolioNotFoundError,
        )

        controller, _, view, background, load_portfolio, _ = _montar()
        view.current_tickers = []
        load_portfolio.execute.side_effect = PortfolioNotFoundError()
        controller.on_load_data()
        _concluir(background)

        assert view.status is not None
        assert "não foi possível" in view.status[0].lower()


class TestProgressoCarga:
    def test_barra_recebe_progresso_do_worker(self):
        controller, _, view, background, _, _ = _montar()
        controller.on_index_clicked("IBOV")
        _concluir(background)

        assert view.progress_updates > 0
        assert view.progress is not None
        assert view.progress[1] > 0


class TestEncadeamentoFundamentalista:
    def test_resultado_encadeia_analise_fundamental(self):
        controller, presenter, _, background, _, _ = _montar()
        controller._iniciar_analise_fundamental = MagicMock()
        controller.on_index_clicked("IBOV")
        _concluir(background)

        controller._iniciar_analise_fundamental.assert_called_once_with(
            ["PETR4", "VALE3"], REFERENCIA, {"PETR4": {"daily_data": []}},
        )


class TestErroGenericoCarga:
    def test_excecao_generica_chama_on_technical_error(self):
        controller, _, view, background, load_portfolio, _ = _montar()
        load_portfolio.execute.side_effect = RuntimeError("bug")
        controller.on_index_clicked("IBOV")
        _concluir(background)

        assert view.status is not None
        assert "Erro técnico" in view.status[0]
        controller._logger.error.assert_called_once()

    def test_portfolio_not_found_de_indice_menciona_indice(self):
        from flowscope.application.load_portfolio_use_case import (
            PortfolioNotFoundError,
        )

        controller, _, view, background, load_portfolio, _ = _montar()
        load_portfolio.execute.side_effect = PortfolioNotFoundError()
        controller.on_index_clicked("IBOV")
        _concluir(background)

        assert view.status is not None
        assert "IBOV" in view.status[0]


class TestCarteiraTickerEdit:
    def test_sem_tickers_submete_carga_de_portfolio(self):
        controller, presenter, view, background, load_portfolio, _ = _montar()
        view.current_tickers = []
        controller.on_ticker_edit()

        handle = background.jobs_ativos[0]
        assert handle.grupo == "carga"
        _concluir(background)
        assert view.tickers == ["PETR4", "VALE3"]
        assert view.flash[-1] == ("Filtro aplicado!", "ℹ")

    def test_com_tickers_aplica_filtro_sem_rede(self):
        controller, _, view, background, load_portfolio, _ = _montar()
        view.current_tickers = ["PETR4"]
        view.chart = MagicMock()
        controller.on_ticker_edit()

        load_portfolio.execute.assert_not_called()
        assert background.jobs_ativos == ()
        assert view.chart.updated is True
        assert view.flash[-1] == ("Filtro aplicado!", "ℹ")

    def test_portfolio_ausente_faz_flash(self):
        controller, _, view, background, load_portfolio, _ = _montar()
        from flowscope.application.load_portfolio_use_case import (
            PortfolioNotFoundError,
        )

        view.current_tickers = []
        load_portfolio.execute.side_effect = PortfolioNotFoundError()
        controller.on_ticker_edit()
        _concluir(background)

        assert view.flash[-1][1] == "⚠"
