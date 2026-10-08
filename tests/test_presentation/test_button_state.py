import os
import threading
import time
import tkinter as tk
import types
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui.app_layout import LayoutMixin
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.charts.document_tree_panel import DocumentTreePanel


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class _CursorGUI(tk.Tk, StatusMixin):
    pass


class _DisableHost(tk.Tk, StatusMixin):
    pass


class TestDisableIdempotente:
    @needs_display
    def test_nao_sobrescreve_snapshot_ativo(self):
        gui = _DisableHost()
        try:
            gui._flash_after_id = None
            gui._load_button = tk.Button(gui, state=tk.NORMAL)
            gui._today_button = tk.Button(gui, state=tk.NORMAL)
            gui._shortcut_btn = None
            gui._copy_data_btn = tk.Button(gui, state=tk.NORMAL)
            gui._ticker_list = MagicMock()
            gui._ticker_list.all_buttons.return_value = []
            gui._period_combo = ttk.Combobox(gui, state="readonly")
            gui._sampling_combo = ttk.Combobox(gui, state="readonly")
            gui._date_entry = ttk.Entry(gui)

            gui.disable_all_buttons()
            gui.disable_all_buttons()
            gui.restore_all_buttons()

            assert gui._load_button.cget("state") == tk.NORMAL
            assert str(gui._period_combo.cget("state")) == "readonly"
            assert str(gui._date_entry.cget("state")) == "normal"
        finally:
            gui.destroy()


class TestDisableDocumentosBotoes:
    @needs_display
    def test_botoes_documentos_desabilitados_e_restaurados(self):
        gui = _DisableHost()
        try:
            gui._flash_after_id = None
            gui._load_button = tk.Button(gui, state=tk.NORMAL)
            gui._today_button = tk.Button(gui, state=tk.NORMAL)
            gui._shortcut_btn = None
            gui._copy_data_btn = tk.Button(gui, state=tk.NORMAL)
            gui._ticker_list = MagicMock()
            gui._ticker_list.all_buttons.return_value = []
            gui._period_combo = ttk.Combobox(gui, state="readonly")
            gui._sampling_combo = ttk.Combobox(gui, state="readonly")
            gui._date_entry = ttk.Entry(gui)
            refresh = tk.Button(gui, state=tk.NORMAL)
            abrir = tk.Button(gui, state=tk.NORMAL)
            gui._documents_panel = MagicMock()
            gui._documents_panel.all_buttons.return_value = [refresh, abrir]

            gui.disable_all_buttons()
            assert refresh.cget("state") == tk.DISABLED
            assert abrir.cget("state") == tk.DISABLED

            gui.restore_all_buttons()
            assert refresh.cget("state") == tk.NORMAL
            assert abrir.cget("state") == tk.NORMAL
            gui._documents_panel.refresh_open_button.assert_called_once()
        finally:
            gui.destroy()

    @needs_display
    def test_seletor_modelo_desabilitado_e_restaurado(self, tmp_path):
        gui = _DisableHost()
        try:
            gui._flash_after_id = None
            gui._load_button = tk.Button(gui, state=tk.NORMAL)
            gui._today_button = tk.Button(gui, state=tk.NORMAL)
            gui._shortcut_btn = None
            gui._copy_data_btn = tk.Button(gui, state=tk.NORMAL)
            gui._ticker_list = MagicMock()
            gui._ticker_list.all_buttons.return_value = []
            gui._period_combo = ttk.Combobox(gui, state="readonly")
            gui._sampling_combo = ttk.Combobox(gui, state="readonly")
            gui._date_entry = ttk.Entry(gui)
            gui._documents_panel = DocumentTreePanel(
                gui, catalog=DocumentCatalog(cache_dir=tmp_path)
            )
            seletor = gui._documents_panel._model_selector

            gui.disable_all_buttons()
            assert str(seletor.botao.cget("state")) == "disabled"
            assert str(seletor.combo.cget("state")) == "disabled"

            gui.restore_all_buttons()
            assert str(seletor.botao.cget("state")) == "normal"
            assert str(seletor.combo.cget("state")) == "readonly"
        finally:
            gui.destroy()

    @needs_display
    def test_botao_resumir_desabilitado_e_restaurado(self, tmp_path):
        gui = _DisableHost()
        try:
            gui._flash_after_id = None
            gui._load_button = tk.Button(gui, state=tk.NORMAL)
            gui._today_button = tk.Button(gui, state=tk.NORMAL)
            gui._shortcut_btn = None
            gui._copy_data_btn = tk.Button(gui, state=tk.NORMAL)
            gui._ticker_list = MagicMock()
            gui._ticker_list.all_buttons.return_value = []
            gui._period_combo = ttk.Combobox(gui, state="readonly")
            gui._sampling_combo = ttk.Combobox(gui, state="readonly")
            gui._date_entry = ttk.Entry(gui)
            painel = DocumentTreePanel(
                gui,
                catalog=DocumentCatalog(cache_dir=tmp_path),
                llm_available=lambda: True,
            )
            caminho = tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf"
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_bytes(b"x")
            painel.update("ALZR11")
            gui._documents_panel = painel
            assert str(painel._resumir_btn.cget("state")) == "normal"

            gui.disable_all_buttons()
            assert str(painel._resumir_btn.cget("state")) == "disabled"

            gui.restore_all_buttons()
            assert str(painel._resumir_btn.cget("state")) == "normal"
        finally:
            gui.destroy()


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


class TestWaitCursor:
    @needs_display
    def test_cursor_watch_sobrepoe_e_restaura(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui._set_wait_cursor()
            assert btn.cget("cursor") == "watch"
            gui._clear_wait_cursor()
            assert btn.cget("cursor") == "hand2"
        finally:
            gui.destroy()

    @needs_display
    def test_cursor_watch_nao_repercorre_enquanto_ativo(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui._set_wait_cursor()
            primeiro = dict(gui._cursor_states)
            gui._set_wait_cursor()
            assert gui._cursor_states == primeiro
            gui._clear_wait_cursor()
            assert gui._cursor_states == {}
        finally:
            gui.destroy()

    @needs_display
    def test_enter_e_exit_busy_aplicam_e_restauram_cursor(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui.enter_busy()
            assert btn.cget("cursor") == "watch"
            gui.exit_busy()
            assert btn.cget("cursor") == "hand2"
        finally:
            gui.destroy()

    @needs_display
    def test_baseline_ignora_cursor_transitorio_de_separador(self):
        gui = _CursorGUI()
        try:
            tree = ttk.Treeview(gui, columns=("a",), show="headings")
            tree.pack()
            tree.config(cursor="sb_h_double_arrow")
            gui._set_wait_cursor()
            assert str(tree.cget("cursor")) == "watch"
            gui._clear_wait_cursor()
            assert str(tree.cget("cursor")) == ""
        finally:
            gui.destroy()

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

    @needs_display
    def test_exit_busy_repetido_nao_deixa_residuo(self):
        gui = _CursorGUI()
        try:
            btn = tk.Button(gui, cursor="hand2")
            btn.pack()
            gui.enter_busy()
            gui.exit_busy()
            assert btn.cget("cursor") == "hand2"
            gui.exit_busy()
            assert btn.cget("cursor") == "hand2"
            assert gui._cursor_states == {}
            assert getattr(gui, "_busy_motion_id", None) is None
        finally:
            gui.destroy()


class _FakeWidget:
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

    def __init__(self) -> None:
        self._cursor = ""
        self._cursor_states: dict = {}
        self._busy_motion_id = None
        self._presenter = None

    def cget(self, key: str) -> str:
        if key == "cursor":
            return self._cursor
        raise tk.TclError(key)

    def config(self, **kwargs: object) -> None:
        if "cursor" in kwargs:
            self._cursor = str(kwargs["cursor"])

    def winfo_children(self) -> list:
        return []

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
        novo = _FakeWidget(cursor="hand2")
        StatusMixin._on_busy_motion(host, types.SimpleNamespace(widget=novo))
        assert novo.cget("cursor") == "watch"
        assert novo in host._cursor_states

        host._clear_wait_cursor()
        assert novo.cget("cursor") == "hand2"

    def test_watch_residual_limpo_quando_ocioso(self):
        host = _CursorHost()
        host._presenter = types.SimpleNamespace(is_busy=False)
        host._set_wait_cursor()
        btn = _FakeWidget(cursor="hand2")
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


class _StatusBarHost(tk.Tk, LayoutMixin, StatusMixin):
    """Host mínimo que constrói a barra de status real sem ícones reais."""

    def _load_icon(self, filename: str, size: tuple = (20, 20)) -> object:
        return None


class TestBotaoInterromper:
    @needs_display
    def test_botao_criado_oculto(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            assert host._stop_button.winfo_manager() == ""
            assert host._stop_button_visivel is False
        finally:
            host.destroy()

    @needs_display
    def test_cancellable_mostra_e_oculta_botao(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            host.set_cancellable(True)
            assert host._stop_button.winfo_manager() != ""
            host.set_cancellable(False)
            assert host._stop_button.winfo_manager() == ""
        finally:
            host.destroy()

    @needs_display
    def test_carga_sincrona_nao_exibe_botao(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            host._set_progress(1, 2, "Baixando dados históricos")
            assert host._progress_bar.winfo_manager() != ""
            assert host._stop_button.winfo_manager() == ""
        finally:
            host.destroy()

    @needs_display
    def test_progresso_de_job_cancelavel_exibe_botao(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            host.set_cancellable(True)
            host._set_progress(1, 2, "Fundamentos")
            assert host._progress_bar.winfo_manager() != ""
            assert host._stop_button.winfo_manager() != ""
        finally:
            host.destroy()

    @needs_display
    def test_status_e_clear_ocultam_botao(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            host.set_cancellable(True)
            host._set_progress(1, 2, "Fundamentos")
            host._set_status("Pronto.")
            assert host._progress_bar.winfo_manager() == ""
            assert host._stop_button.winfo_manager() == ""
            host.set_cancellable(True)
            host._set_progress(1, 2, "Fundamentos")
            host.clear_progress()
            assert host._stop_button.winfo_manager() == ""
        finally:
            host.destroy()

    @needs_display
    def test_clique_solicita_cancelamento_ao_presenter(self):
        host = _StatusBarHost()
        try:
            host._build_statusbar()
            host._presenter = MagicMock()
            host._on_stop_clicked()
            host._presenter.request_cancel.assert_called_once()
        finally:
            host.destroy()


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
