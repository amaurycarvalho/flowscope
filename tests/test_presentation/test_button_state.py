import os
import threading
import time
import tkinter as tk
import types
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.background.manager import BackgroundManager


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class _CursorGUI(tk.Tk, StatusMixin):
    pass


class _FakeWidget:
    """Widget mínimo (sem Tk) para cursor, estado e empacotamento."""

    def __init__(self, cursor: str = "", state: str = "normal") -> None:
        self._cursor = cursor
        self._state = state
        self._packed = False
        self._opcoes: dict = {}

    def cget(self, key: str) -> str:
        if key == "cursor":
            return self._cursor
        if key == "state":
            return self._state
        raise tk.TclError(key)

    def config(self, **kwargs: object) -> None:
        if "cursor" in kwargs:
            self._cursor = str(kwargs["cursor"])
        if "state" in kwargs:
            self._state = kwargs["state"]

    def __setitem__(self, key: str, value: object) -> None:
        self._opcoes[key] = value

    def __getitem__(self, key: str) -> object:
        return self._opcoes[key]

    def pack(self, **_kwargs: object) -> None:
        self._packed = True

    def pack_forget(self) -> None:
        self._packed = False

    def winfo_ismapped(self) -> int:
        return 1 if self._packed else 0

    def winfo_manager(self) -> str:
        return "pack" if self._packed else ""

    def winfo_children(self) -> list:
        return []


class _DisableHost(StatusMixin):
    """Host headless com widgets fake para bloqueio/restauração de botões."""

    def __init__(self) -> None:
        self._flash_after_id = None
        self._load_button = _FakeWidget()
        self._today_button = _FakeWidget()
        self._shortcut_btn = None
        self._copy_data_btn = _FakeWidget()
        self._ticker_list = MagicMock()
        self._ticker_list.all_buttons.return_value = []
        self._period_combo = _FakeWidget(state="readonly")
        self._sampling_combo = _FakeWidget(state="readonly")
        self._date_entry = _FakeWidget(state="normal")

    def after_cancel(self, _id: object) -> None:
        pass


class TestDisableIdempotente:
    def test_nao_sobrescreve_snapshot_ativo(self):
        gui = _DisableHost()

        gui.disable_all_buttons()
        gui.disable_all_buttons()
        gui.restore_all_buttons()

        assert gui._load_button.cget("state") == tk.NORMAL
        assert gui._period_combo.cget("state") == "readonly"
        assert gui._date_entry.cget("state") == "normal"


class TestDisableDocumentosBotoes:
    def test_botoes_documentos_desabilitados_e_restaurados(self):
        gui = _DisableHost()
        refresh = _FakeWidget()
        abrir = _FakeWidget()
        gui._documents_panel = MagicMock()
        gui._documents_panel.all_buttons.return_value = [refresh, abrir]

        gui.disable_all_buttons()
        assert refresh.cget("state") == tk.DISABLED
        assert abrir.cget("state") == tk.DISABLED

        gui.restore_all_buttons()
        assert refresh.cget("state") == tk.NORMAL
        assert abrir.cget("state") == tk.NORMAL
        gui._documents_panel.refresh_open_button.assert_called_once()

    def test_seletor_modelo_desabilitado_e_restaurado(self):
        gui = _DisableHost()
        botao = _FakeWidget(state="normal")
        combo = _FakeWidget(state="readonly")
        gui._documents_panel = MagicMock()
        gui._documents_panel.all_buttons.return_value = [botao, combo]

        gui.disable_all_buttons()
        assert botao.cget("state") == tk.DISABLED
        assert combo.cget("state") == tk.DISABLED

        gui.restore_all_buttons()
        assert botao.cget("state") == "normal"
        assert combo.cget("state") == "readonly"

    def test_botao_resumir_desabilitado_e_restaurado(self):
        gui = _DisableHost()
        resumir = _FakeWidget(state="normal")
        gui._documents_panel = MagicMock()
        gui._documents_panel.all_buttons.return_value = [resumir]

        gui.disable_all_buttons()
        assert resumir.cget("state") == tk.DISABLED

        gui.restore_all_buttons()
        assert resumir.cget("state") == "normal"


class _FundamentalCursorHost(tk.Tk, StatusMixin):
    def disable_all_buttons(self) -> None:
        pass

    def restore_all_buttons(self) -> None:
        pass

    def clear_progress(self) -> None:
        pass

    def set_cancellable(self, cancellable: bool) -> None:
        pass

    def config_copy_button_state(self, state: str) -> None:
        pass


class TestWaitCursorFundamentos:
    @needs_display
    def test_cursor_treeview_restaurado_apos_substituicao_de_job(self):
        from flowscope.presentation.gui.presenter import FlowScopePresenter

        gui = _FundamentalCursorHost()
        try:
            tree = ttk.Treeview(gui, columns=("ticker",), show="headings")
            tree.pack()
            tree.config(cursor="hand2")
            presenter = FlowScopePresenter(gui)

            presenter.on_operation_started()
            presenter.on_fundamental_started()
            presenter.on_operation_finished()
            presenter.on_fundamental_started()
            presenter.on_fundamental_finished()
            assert str(tree.cget("cursor")) == "watch"

            presenter.on_fundamental_finished()
            assert str(tree.cget("cursor")) == "hand2"
        finally:
            gui.destroy()


class TestWaitCursorHeadless:
    def _host(self, widget=None):
        filhos = [widget] if widget is not None else []
        return _CursorHost(filhos)

    def test_cursor_watch_sobrepoe_e_restaura(self):
        btn = _FakeWidget(cursor="hand2")
        gui = self._host(btn)
        gui._set_wait_cursor()
        assert btn.cget("cursor") == "watch"
        gui._clear_wait_cursor()
        assert btn.cget("cursor") == "hand2"

    def test_cursor_watch_nao_repercorre_enquanto_ativo(self):
        gui = self._host(_FakeWidget(cursor="hand2"))
        gui._set_wait_cursor()
        primeiro = dict(gui._cursor_states)
        gui._set_wait_cursor()
        assert gui._cursor_states == primeiro
        gui._clear_wait_cursor()
        assert gui._cursor_states == {}

    def test_enter_e_exit_busy_aplicam_e_restauram_cursor(self):
        btn = _FakeWidget(cursor="hand2")
        gui = self._host(btn)
        gui.enter_busy()
        assert btn.cget("cursor") == "watch"
        gui.exit_busy()
        assert btn.cget("cursor") == "hand2"

    def test_baseline_ignora_cursor_transitorio_de_separador(self):
        tree = _FakeWidget(cursor="sb_h_double_arrow")
        gui = self._host(tree)
        gui._set_wait_cursor()
        assert tree.cget("cursor") == "watch"
        gui._clear_wait_cursor()
        assert tree.cget("cursor") == ""

    def test_exit_busy_repetido_nao_deixa_residuo(self):
        btn = _FakeWidget(cursor="hand2")
        gui = self._host(btn)
        gui.enter_busy()
        gui.exit_busy()
        assert btn.cget("cursor") == "hand2"
        gui.exit_busy()
        assert btn.cget("cursor") == "hand2"
        assert gui._cursor_states == {}
        assert getattr(gui, "_busy_motion_id", None) is None


class TestWaitCursorMotion:
    @needs_display
    def test_motion_sobre_separador_e_sash_mantem_watch(self):
        gui = _CursorGUI()
        try:
            tree = ttk.Treeview(gui, columns=("a", "b"), show="headings")
            tree.heading("a", text="A")
            tree.heading("b", text="B")
            tree.column("a", width=80)
            tree.column("b", width=80)
            tree.pack()

            pw = tk.PanedWindow(gui, orient=tk.HORIZONTAL)
            pw.pack(fill=tk.BOTH, expand=True)
            pw.add(tk.Frame(pw, width=50))
            pw.add(tk.Frame(pw, width=50))
            gui.update()

            gui._set_wait_cursor()

            sep_x = next(
                x for x in range(tree.winfo_width())
                if tree.identify_region(x, 5) == "separator"
            )
            tree.event_generate("<Motion>", x=sep_x, y=5)
            gui.update()
            assert str(tree.cget("cursor")) == "watch"

            sx, sy = pw.sash_coord(0)
            pw.event_generate("<Motion>", x=sx + 1, y=sy)
            gui.update()
            assert str(pw.cget("cursor")) == "watch"

            gui._clear_wait_cursor()
        finally:
            gui.destroy()


class _FakeWidgetCursor:
    """Widget mínimo (sem Tk) para exercitar a máquina de cursor."""

    def __init__(self, cursor: str = "") -> None:
        self._cursor = cursor

    def cget(self, key: str) -> str:
        if key == "cursor":
            return self._cursor
        raise tk.TclError(key)

    def config(self, **kwargs: object) -> None:
        if "cursor" in kwargs:
            self._cursor = str(kwargs["cursor"])

    def winfo_children(self) -> list:
        return []


class _CursorHost(StatusMixin):
    """Host sem display que implementa o mínimo usado pelo ``StatusMixin``."""

    def __init__(self, children: list | None = None) -> None:
        self._cursor = ""
        self._cursor_states: dict = {}
        self._busy_motion_id = None
        self._presenter = None
        self._children = list(children or [])

    def cget(self, key: str) -> str:
        if key == "cursor":
            return self._cursor
        raise tk.TclError(key)

    def config(self, **kwargs: object) -> None:
        if "cursor" in kwargs:
            self._cursor = str(kwargs["cursor"])

    def winfo_children(self) -> list:
        return list(self._children)

    def bind(self, sequence: str, func: object, add: str | None = None) -> str:
        return "hook"

    def unbind(self, sequence: str, funcid: object = None) -> None:
        pass

    def deletecommand(self, funcid: object = None) -> None:
        pass

    def update_idletasks(self) -> None:
        pass


class TestCursorBusyHeadless:
    def test_widget_criado_durante_busy_restaura(self):
        host = _CursorHost()
        host._set_wait_cursor()
        novo = _FakeWidgetCursor(cursor="hand2")
        StatusMixin._on_busy_motion(host, types.SimpleNamespace(widget=novo))
        assert novo.cget("cursor") == "watch"
        assert novo in host._cursor_states

        host._clear_wait_cursor()
        assert novo.cget("cursor") == "hand2"

    def test_watch_residual_limpo_quando_ocioso(self):
        host = _CursorHost()
        host._presenter = types.SimpleNamespace(is_busy=False)
        host._set_wait_cursor()
        btn = _FakeWidgetCursor(cursor="hand2")
        host._cursor_states[btn] = "hand2"
        btn.config(cursor="watch")

        StatusMixin._on_busy_motion(host, types.SimpleNamespace(widget=btn))

        assert btn.cget("cursor") == "hand2"
        assert host._cursor_states == {}
        assert host._busy_motion_id is None

    def test_remove_hook_usa_unbind_especifico(self):
        host = _CursorHost()
        host._busy_motion_id = "hook123"
        chamadas = []
        host.unbind = lambda seq, fid=None: chamadas.append((seq, fid))

        StatusMixin._remover_hook_motion_busy(host)

        assert chamadas == [("<Motion>", "hook123")]
        assert host._busy_motion_id is None


class TestManagersLocaisNaoAcionamCursorHeadless:
    def test_manager_local_nao_aciona_cursor_global(self):
        from flowscope.presentation.gui.presenter import FlowScopePresenter

        view = MagicMock()
        presenter = FlowScopePresenter(view)

        global_mgr = BackgroundManager()
        global_mgr.ao_iniciar(lambda h: presenter.enter())
        global_mgr.ao_terminar(lambda h: presenter.exit())
        global_mgr.submit(lambda ctx: None, grupo="g")
        prazo = time.time() + 2
        while not view.exit_busy.called and time.time() < prazo:
            global_mgr.drenar()
            time.sleep(0.01)
        view.enter_busy.assert_called_once()
        view.exit_busy.assert_called_once()

        view.reset_mock()
        concluido = threading.Event()
        local_mgr = BackgroundManager()
        local_mgr.submit(lambda ctx: concluido.set(), grupo="local")
        prazo = time.time() + 2
        while not concluido.is_set() and time.time() < prazo:
            local_mgr.drenar()
            time.sleep(0.01)
        local_mgr.drenar()
        view.enter_busy.assert_not_called()
        view.exit_busy.assert_not_called()


class _StatusVarFake:
    """Variável Tk mínima que armazena o texto definido."""

    def __init__(self) -> None:
        self.value = ""

    def set(self, valor: object) -> None:
        self.value = str(valor)

    def get(self) -> str:
        return self.value


class _StatusHost(StatusMixin):
    """Host headless da barra de status com widgets fake."""

    def __init__(self) -> None:
        self._status_var = _StatusVarFake()
        self._progress_bar = _FakeWidget()
        self._stop_button = _FakeWidget()
        self._stop_button_visivel = False

    def update_idletasks(self) -> None:
        pass


class TestBotaoInterromper:
    def test_botao_criado_oculto(self):
        host = _StatusHost()
        assert host._stop_button.winfo_manager() == ""
        assert host._stop_button_visivel is False

    def test_cancellable_mostra_e_oculta_botao(self):
        host = _StatusHost()
        host.set_cancellable(True)
        assert host._stop_button.winfo_manager() != ""
        host.set_cancellable(False)
        assert host._stop_button.winfo_manager() == ""

    def test_carga_sincrona_nao_exibe_botao(self):
        host = _StatusHost()
        host._set_progress(1, 2, "Baixando dados históricos")
        assert host._progress_bar.winfo_manager() != ""
        assert host._stop_button.winfo_manager() == ""

    def test_progresso_de_job_cancelavel_exibe_botao(self):
        host = _StatusHost()
        host.set_cancellable(True)
        host._set_progress(1, 2, "Fundamentos")
        assert host._progress_bar.winfo_manager() != ""
        assert host._stop_button.winfo_manager() != ""

    def test_status_e_clear_ocultam_botao(self):
        host = _StatusHost()
        host.set_cancellable(True)
        host._set_progress(1, 2, "Fundamentos")
        host._set_status("Pronto.")
        assert host._progress_bar.winfo_manager() == ""
        assert host._stop_button.winfo_manager() == ""
        host.set_cancellable(True)
        host._set_progress(1, 2, "Fundamentos")
        host.clear_progress()
        assert host._stop_button.winfo_manager() == ""

    def test_clique_solicita_cancelamento_ao_presenter(self):
        host = _StatusHost()
        host._presenter = MagicMock()
        host._on_stop_clicked()
        host._presenter.request_cancel.assert_called_once()


class _TabsCursorHost(tk.Tk, StatusMixin, TabsLayoutMixin):
    """Constrói as abas reais para verificar a cobertura do estado ocupado."""

    def _copy_chart(self, figure: object) -> None:
        pass

    def _on_quadrant_summary(self, *args: object) -> None:
        pass

    def _on_flow_summary(self, *args: object) -> None:
        pass


class TestCoberturaEstadoOcupado:
    @needs_display
    def test_snapshot_cobre_paineis_de_todas_as_abas(self):
        gui = _TabsCursorHost()
        try:
            gui._general_notebook = ttk.Notebook(gui)
            gui._main_notebook = ttk.Notebook(gui)
            gui._general_notebook.pack()
            gui._main_notebook.pack()
            gui._build_general_tabs()
            gui._build_ticker_tabs()
            gui._GENERAL = {
                "VWAP": gui._vwap_chart,
                "Quadrantes": gui._quadrant_chart,
                "Dominância do Pregão": gui._dominance_ranking,
                "Fundamentos": gui._fundamental_table,
            }
            gui._TICKER = {
                "Evolução da Dominância": gui._dominance_timeline,
                "Amplitude de Preço": gui._price_range_panel,
                "Fluxo Financeiro": gui._financial_flow_panel,
                "Evolução dos Fundamentos": gui._fundamental_evolution_panel,
                "Documentos": gui._documents_panel,
            }
            gui.update()

            gui._set_wait_cursor()
            cobertos = set(gui._cursor_states)
            assert len(cobertos) > 0
            for painel in [*gui._GENERAL.values(), *gui._TICKER.values()]:
                assert painel.frame in cobertos
            gui._clear_wait_cursor()
        finally:
            gui.destroy()
