import os
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.charts.document_tree_panel import DocumentTreePanel


@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class TestDisableRestoreButtons:
    @needs_display
    def test_disable_all_salva_snapshot_e_desabilita(self, root):
        btn1 = tk.Button(root, state=tk.NORMAL)
        btn2 = tk.Button(root, state=tk.DISABLED)
        btn3 = tk.Button(root, state=tk.ACTIVE)

        gui = _FakeGUI(root, [btn1, btn2, btn3])

        gui.disable_all_buttons()

        assert btn1.cget("state") == tk.DISABLED
        assert btn2.cget("state") == tk.DISABLED
        assert btn3.cget("state") == tk.DISABLED
        assert gui._button_states[btn1] == tk.NORMAL
        assert gui._button_states[btn2] == tk.DISABLED
        assert gui._button_states[btn3] == tk.ACTIVE

    @needs_display
    def test_restore_all_retorna_aos_estados_anteriores(self, root):
        btn1 = tk.Button(root, state=tk.NORMAL)
        btn2 = tk.Button(root, state=tk.DISABLED)

        gui = _FakeGUI(root, [btn1, btn2])
        gui.disable_all_buttons()
        gui.restore_all_buttons()

        assert btn1.cget("state") == tk.NORMAL
        assert btn2.cget("state") == tk.DISABLED


class _FakeGUI:
    def __init__(self, root, buttons):
        self._button_states: dict[tk.Widget, str] = {}
        self._buttons = buttons

    def disable_all_buttons(self) -> None:
        self._button_states = {}
        for btn in self._buttons:
            self._button_states[btn] = btn.cget("state")
            btn.config(state=tk.DISABLED)

    def restore_all_buttons(self) -> None:
        if not hasattr(self, "_button_states"):
            return
        for widget, state in self._button_states.items():
            try:
                widget.config(state=state)
            except tk.TclError:
                pass
        self._button_states = {}


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
    def test_botao_ia_desabilitado_e_restaurado(self, tmp_path):
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

            gui.disable_all_buttons()
            assert (
                str(gui._documents_panel._ia_btn.cget("state")) == "disabled"
            )

            gui.restore_all_buttons()
            assert str(gui._documents_panel._ia_btn.cget("state")) == "normal"
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
