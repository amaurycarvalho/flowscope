"""Construção do layout da interface gráfica do FlowScope."""

import platform
import tkinter as tk
from datetime import datetime, timezone
from tkinter import ttk

from PIL import Image, ImageTk
from tkcalendar import DateEntry

from flowscope.presentation.gui.app_constants import PAD, PAD_LARGE, PAD_SMALL
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.widgets.orientation_panel import OrientationPanel
from flowscope.presentation.gui.widgets.ticker_list import TickerList
from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope.presentation.main import (
    _desktop_shortcut_exists,
    _resolve_icon_path,
)


class LayoutMixin:
    """Constrói os componentes visuais da janela principal."""

    def _load_icon(self: "LayoutMixin", filename: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
        path = _resolve_icon_path(filename)
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        if not hasattr(self, "_icon_refs"):
            self._icon_refs = []
        self._icon_refs.append(photo)
        return photo

    def _set_icon(self: "LayoutMixin") -> None:
        system = platform.system()
        if system == "Linux":
            png = _resolve_icon_path("flowscope.png")
            if png.exists():
                try:
                    img = tk.PhotoImage(file=str(png))
                    self.wm_iconphoto(True, img)
                except tk.TclError:
                    pass
        elif system == "Windows":
            ico = _resolve_icon_path("flowscope.ico")
            if ico.exists():
                try:
                    self.iconbitmap(str(ico))
                except tk.TclError:
                    pass

    def _setup_style(self: "LayoutMixin") -> None:
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("TkDefaultFont", 9, "bold"))

    def _build_top_bar(self: "LayoutMixin") -> None:
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=PAD_LARGE, pady=PAD_SMALL)

        tk.Label(top, text="Data de referência:").pack(side=tk.LEFT)
        self._date_entry = DateEntry(
            top,
            date_pattern="yyyy-MM-dd",
            maxdate=datetime.now(timezone.utc).date(),
        )
        self._date_entry.pack(side=tk.LEFT, padx=PAD_SMALL)
        self._today_button = tk.Button(
            top, image=self._load_icon("document-open-recent.png"),
            command=self._on_today, cursor="hand2", padx=0,
        )
        self._today_button.pack(side=tk.LEFT, padx=(0, PAD_SMALL))
        self._load_button = tk.Button(
            top, image=self._load_icon("view-refresh.png"),
            command=self._on_load_data, cursor="hand2", padx=0,
        )
        self._load_button.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._period_var = tk.StringVar(value="Últimos 30 dias")
        self._period_combo = ttk.Combobox(
            top, textvariable=self._period_var,
            values=["Últimos 30 dias", "Últimos 60 dias (cache)", "Últimos 90 dias (cache)"],
            state="readonly", width=18,
        )
        self._period_combo.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._sampling_var = tk.StringVar(value="Fibonacci")
        self._sampling_combo = ttk.Combobox(
            top, textvariable=self._sampling_var,
            values=["Fibonacci", "Fibonacci reverso", "Fibonacci duplo",
                    "Monte Carlo", "Monte Carlo duplo", "Todos os dias"],
            state="readonly", width=18,
        )
        self._sampling_combo.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._copy_data_btn = tk.Button(
            top, image=self._load_icon("edit-copy.png"),
            command=self._copy_data,
            state=tk.DISABLED, cursor="hand2", padx=0,
        )
        self._copy_data_btn.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._shortcut_btn = None
        if platform.system() == "Linux" and not _desktop_shortcut_exists():
            self._shortcut_btn = tk.Button(
                top, text="Criar atalho no desktop",
                command=self._on_create_shortcut, cursor="hand2",
            )
            self._shortcut_btn.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._date_label = tk.Label(top, text="", fg="gray")
        self._date_label.pack(side=tk.LEFT, padx=PAD)
        ToolTip(self._today_button, "Voltar para a data atual")
        ToolTip(self._load_button, "Carregar dados da data selecionada")
        ToolTip(self._date_entry, "Data de referência para carregamento")
        ToolTip(self._period_combo, "Seleciona a janela de tempo para análise dos dados históricos")
        ToolTip(self._sampling_combo, "Define o método de seleção das datas dentro do período")
        ToolTip(self._copy_data_btn, "Copiar dados CSV para a área de transferência")

        self._sampling_label = tk.Label(top, text="", fg="gray")
        self._sampling_label.pack(side=tk.LEFT, padx=PAD)
        self._update_sampling_label()

        self._period_combo.bind("<<ComboboxSelected>>", self._on_period_combo_changed)
        self._sampling_combo.bind("<<ComboboxSelected>>", self._on_sampling_combo_changed)

    def _build_main_area(self: "LayoutMixin") -> None:
        self._main_pw = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=PAD_LARGE, pady=PAD_SMALL)

        self._left_pw = tk.PanedWindow(
            self._main_pw, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.add(self._left_pw, stretch="always")

        self._main_notebook = ttk.Notebook(self._left_pw)
        self._left_pw.add(self._main_notebook, stretch="always")

        general_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(general_frame, text="Análise Geral")

        self._general_notebook = ttk.Notebook(general_frame)
        self._general_notebook.pack(fill=tk.BOTH, expand=True)

        self._build_general_tabs()
        self._build_ticker_tabs()

        self._tab_content = TAB_CONTENT

        self._main_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._general_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._ticker_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        last_tab = self._prefs.get("last_tab", "Análise Geral")
        last_subtab = self._prefs.get("last_subtab", "VWAP")
        self.after(10, lambda: self._restore_tabs(last_tab, last_subtab))

        right_pw = tk.PanedWindow(
            self._main_pw, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.add(right_pw, stretch="never")

        ticker_frame = tk.Frame(right_pw)
        right_pw.add(ticker_frame, stretch="always")
        self._ticker_list = TickerList(
            ticker_frame,
            initialdir=self._prefs.get("last_ticker_dir"),
            on_dir_changed=self._on_ticker_dir_changed,
            on_index_click={
                "IBOV": lambda: None,
                "IDIV": lambda: None,
                "IFIX": lambda: None,
            },
        )
        self._ticker_list.frame.pack(fill=tk.BOTH, expand=True)

        analysis_frame = tk.Frame(right_pw)
        right_pw.add(analysis_frame, stretch="never")
        self._orientation_panel = OrientationPanel(analysis_frame)
        self._orientation_panel.frame.pack(fill=tk.X)

        if self._prefs.get("sash_positions"):
            try:
                pos = self._prefs["sash_positions"]
                if isinstance(pos, (list, tuple)) and len(pos) >= 4:
                    self.after(100, lambda: self._restore_sashes(pos))
            except tk.TclError:
                pass

        self._GENERAL = {
            "VWAP": self._vwap_chart,
            "Quadrantes": self._quadrant_chart,
            "Dominância do Pregão": self._dominance_ranking,
        }
        self._TICKER = {
            "Evolução da Dominância": self._dominance_timeline,
            "Amplitude de Preço": self._price_range_panel,
            "Fluxo Financeiro": self._financial_flow_panel,
        }
        self._ticker_charts = set(self._TICKER.values())
        self._all_charts = [*self._GENERAL.values(), *self._TICKER.values()]

    def _build_statusbar(self: "LayoutMixin") -> None:
        self._status_var = tk.StringVar()
        self._status_frame = tk.Frame(self, relief=tk.SUNKEN, bd=1)
        self._status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_label = tk.Label(
            self._status_frame,
            textvariable=self._status_var,
            anchor=tk.W,
            padx=PAD_SMALL,
            pady=PAD_SMALL,
        )
        self._status_label.pack(side=tk.LEFT)

        self._progress_bar = ttk.Progressbar(
            self._status_frame,
            mode="determinate",
            length=140,
        )

    def _bind_shortcuts(self: "LayoutMixin") -> None:
        self._date_entry.bind("<Return>", lambda e: self._on_load_data())
        self.bind_all("<Control-Shift-c>", lambda e: self._copy_data())
        self.bind_all("<F5>", lambda e: self._on_load_data())
