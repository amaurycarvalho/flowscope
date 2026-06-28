import json
import platform
import tkinter as tk
import tkinter.ttk as ttk
from datetime import date, datetime
from pathlib import Path
from tkcalendar import DateEntry

from flowscope.application.use_cases import AnalyzeTickersUseCase
from flowscope.infrastructure.b3.client import B3Client
from flowscope.infrastructure.b3.repository import B3DataRepository
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart
from flowscope.presentation.gui.widgets.orientation_panel import OrientationPanel
from flowscope.presentation.gui.widgets.ticker_list import TickerList
from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope import __version__

TITLE_PREFIX = f"FlowScope v{__version__}"

PAD_SMALL = 4
PAD = 8
PAD_LARGE = 12

CONFIG_DIR = Path.home() / ".flowscope"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "last_date": None,
    "last_tab": "Análise Geral",
    "last_subtab": "VWAP",
    "window_geometry": None,
    "sash_positions": None,
    "last_ticker_dir": None,
}


def load_preferences() -> dict:
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **data}
    except (json.JSONDecodeError, OSError):
        pass
    return dict(DEFAULT_CONFIG)


def save_preferences(data: dict) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    except OSError:
        pass


class FlowScopeGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITLE_PREFIX)
        self._prefs = load_preferences()

        if self._prefs.get("window_geometry"):
            self.geometry(self._prefs["window_geometry"])
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            w = int(screen_w * 0.8)
            h = int(screen_h * 0.8)
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
            self.minsize(w, h)

        self.resizable(True, True)
        if platform.system() == "Linux":
            self.wm_attributes("-type", "normal")

        self._set_icon()
        self._setup_style()

        self._repo = B3DataRepository(B3Client())
        self._use_case = AnalyzeTickersUseCase(self._repo)
        self._current_data: dict = {}
        self._tickers: list[str] = []
        self._all_tickers: list[str] = []
        self._loading_after_id = None
        self._flash_after_id = None

        self._build_top_bar()
        self._build_main_area()
        self._build_statusbar()
        self._build_action_buttons()
        self._bind_shortcuts()

        if self._prefs.get("last_date"):
            try:
                self._date_entry.set_date(
                    datetime.strptime(self._prefs["last_date"], "%Y-%m-%d").date()
                )
            except (ValueError, TypeError):
                pass

        self._date_entry.focus_set()
        self._set_status("Pronto. Selecione uma data e clique em Carregar.")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_icon(self):
        icon_dir = Path(__file__).resolve().parent.parent.parent / "icons"
        system = platform.system()
        if system == "Linux":
            png = icon_dir / "flowscope.png"
            if png.exists():
                try:
                    img = tk.PhotoImage(file=str(png))
                    self.wm_iconphoto(True, img)
                except tk.TclError:
                    pass
        elif system == "Windows":
            ico = icon_dir / "flowscope.ico"
            if ico.exists():
                try:
                    self.iconbitmap(str(ico))
                except tk.TclError:
                    pass

    def _setup_style(self):
        style = ttk.Style()
        style.configure("TLabelframe.Label", font=("TkDefaultFont", 9, "bold"))

    def _build_top_bar(self):
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=PAD_LARGE, pady=PAD_SMALL)

        tk.Label(top, text="Data de referência:").pack(side=tk.LEFT)
        self._date_entry = DateEntry(
            top,
            date_pattern="yyyy-MM-dd",
            maxdate=date.today(),
        )
        self._date_entry.pack(side=tk.LEFT, padx=PAD_SMALL)
        self._today_button = tk.Button(
            top, text="Hoje", command=self._on_today, cursor="hand2"
        )
        self._today_button.pack(side=tk.LEFT, padx=(0, PAD_SMALL))
        self._load_button = tk.Button(
            top, text="Carregar", command=self._on_load_data, cursor="hand2"
        )
        self._load_button.pack(side=tk.LEFT, padx=PAD_SMALL)

        self._date_label = tk.Label(top, text="", fg="gray")
        self._date_label.pack(side=tk.LEFT, padx=PAD)
        ToolTip(self._today_button, "Voltar para a data atual")
        ToolTip(self._load_button, "Carregar dados da data selecionada")
        ToolTip(self._date_entry, "Data de referência para carregamento")

    def _build_main_area(self):
        self._main_pw = tk.PanedWindow(
            self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=PAD_LARGE, pady=PAD_SMALL)

        left_pw = tk.PanedWindow(
            self._main_pw, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.add(left_pw, stretch="always")

        self._main_notebook = ttk.Notebook(left_pw)
        left_pw.add(self._main_notebook, stretch="always")

        general_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(general_frame, text="Análise Geral")

        self._general_notebook = ttk.Notebook(general_frame)
        self._general_notebook.pack(fill=tk.BOTH, expand=True)

        general_vwap_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_vwap_frame, text="VWAP")
        self._vwap_chart = VWAPHistChart(general_vwap_frame)
        self._vwap_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_quadrantes_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_quadrantes_frame, text="Quadrantes")
        ttk.Label(
            general_quadrantes_frame, text="Em desenvolvimento.",
            font=("TkDefaultFont", 12), foreground="gray",
        ).pack(expand=True)

        ticker_main_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(ticker_main_frame, text="Análise do Ticker")

        self._ticker_combo = ttk.Combobox(
            ticker_main_frame, state="readonly",
        )
        self._ticker_combo.pack(fill=tk.X, padx=PAD_SMALL, pady=PAD_SMALL)

        self._ticker_notebook = ttk.Notebook(ticker_main_frame)
        self._ticker_notebook.pack(fill=tk.BOTH, expand=True)

        tab_names = [
            "Dominância do Pregão",
            "Fluxo Financeiro",
            "Participação Institucional",
            "Eficiência do Movimento",
            "Resumo Geral",
        ]
        for name in tab_names:
            frame = ttk.Frame(self._ticker_notebook)
            self._ticker_notebook.add(frame, text=name)
            ttk.Label(
                frame, text="Em desenvolvimento.",
                font=("TkDefaultFont", 12), foreground="gray",
            ).pack(expand=True)

        self._tab_content = {
            ("Análise Geral", "VWAP"): (
                "VWAP — Volume Weighted Average Price",
                "Objetivo: Identificar o preço médio ponderado pelo volume negociado no período, revelando o valor justo da ação sob a ótica do fluxo de ordens.\n\n"
                "Indicadores envolvidos: VWAP (preço médio ponderado), volume por bucket de preço (volume profile), preço de fechamento (LastPric), preço mínimo e máximo (MinPric, MaxPric).\n\n"
                "Como interpretar: O VWAP é a referência de preço justo do período. Negociações acima do VWAP indicam viés comprador; abaixo, viés vendedor. "
                "A largura do violino mostra em quais faixas de preço houve maior concentração de volume. "
                "O último preço (losango vermelho) em relação ao VWAP indica se o fechamento reforça ou contradiz a tendência do período."
            ),
            ("Análise Geral", "Quadrantes"): (
                "Quadrantes",
                "Em desenvolvimento. Este painel classificará os ativos em quadrantes com base em indicadores de fluxo e preço."
            ),
            ("Análise do Ticker", "Dominância do Pregão"): (
                "Dominância do Pregão",
                "Em desenvolvimento. Este painel analisará a participação relativa do ticker no volume total do pregão."
            ),
            ("Análise do Ticker", "Fluxo Financeiro"): (
                "Fluxo Financeiro",
                "Em desenvolvimento. Este painel exibirá o fluxo de capital (compras vs vendas) ao longo do pregão."
            ),
            ("Análise do Ticker", "Participação Institucional"): (
                "Participação Institucional",
                "Em desenvolvimento. Este painel estimará a atividade institucional com base no volume e no delta acumulado."
            ),
            ("Análise do Ticker", "Eficiência do Movimento"): (
                "Eficiência do Movimento",
                "Em desenvolvimento. Este painel avaliará quão eficiente foi o movimento de preço em relação ao volume consumido."
            ),
            ("Análise do Ticker", "Resumo Geral"): (
                "Resumo Geral",
                "Em desenvolvimento. Este painel consolidará os demais indicadores em um resumo qualitativo único por ticker."
            ),
        }

        self._main_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._general_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._ticker_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._ticker_combo.bind("<<ComboboxSelected>>", self._on_tab_changed)

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
            on_change=self._on_ticker_edit,
            initialdir=self._prefs.get("last_ticker_dir"),
            on_dir_changed=self._on_ticker_dir_changed,
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
            except Exception:
                pass

    def _restore_tabs(self, last_tab, last_subtab):
        try:
            for i in range(self._main_notebook.index("end")):
                if self._main_notebook.tab(i, "text") == last_tab:
                    self._main_notebook.select(i)
                    break
            notebook = self._general_notebook if last_tab == "Análise Geral" else self._ticker_notebook
            for i in range(notebook.index("end")):
                if notebook.tab(i, "text") == last_subtab:
                    notebook.select(i)
                    break
        except Exception:
            pass
        self._on_tab_changed()

    def _restore_sashes(self, positions):
        try:
            if len(positions) >= 2:
                self._main_pw.sash_place(0, positions[0], 0)
        except Exception:
            pass

    def _build_action_buttons(self):
        bottom = tk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=PAD_LARGE, pady=PAD_SMALL)

        export_frame = ttk.LabelFrame(bottom, text="Exportação")
        export_frame.pack(fill=tk.X)

        btn_container = tk.Frame(export_frame)
        btn_container.pack(fill=tk.X, padx=PAD_SMALL, pady=PAD_SMALL)

        self._copy_data_btn = tk.Button(
            btn_container,
            text="Copiar Dados",
            command=self._copy_data,
            cursor="hand2",
            padx=PAD,
        )
        self._copy_data_btn.pack(side=tk.LEFT, ipadx=PAD_SMALL, ipady=PAD_SMALL)
        ToolTip(self._copy_data_btn, "Copiar dados CSV para a área de transferência")

        ttk.Separator(btn_container, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=PAD
        )

        self._copy_chart_btn = tk.Button(
            btn_container,
            text="Copiar Gráfico",
            command=self._copy_chart,
            cursor="hand2",
            padx=PAD,
        )
        self._copy_chart_btn.pack(side=tk.LEFT, ipadx=PAD_SMALL, ipady=PAD_SMALL)
        ToolTip(self._copy_chart_btn, "Copiar gráfico como imagem para a área de transferência")

    def _build_statusbar(self):
        self._status_var = tk.StringVar()
        bar = tk.Label(
            self,
            textvariable=self._status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padx=PAD_SMALL,
            pady=PAD_SMALL,
        )
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _set_status(self, msg: str, icon: str = "") -> None:
        text = f"{icon} {msg}" if icon else msg
        self._status_var.set(text)

    def _flash_status(self, msg: str, icon: str = "✓", clear_ms: int = 2500) -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
        self._set_status(msg, icon)
        self._flash_after_id = self.after(clear_ms, lambda: self._set_status("Pronto."))

    def _enter_loading_state(self):
        self._load_button.config(state=tk.DISABLED)
        self._today_button.config(state=tk.DISABLED)
        self._date_entry.config(state=tk.DISABLED)
        self.config(cursor="watch")
        self.update_idletasks()
        self._animate_loading()

    def _exit_loading_state(self):
        self._load_button.config(state=tk.NORMAL)
        self._today_button.config(state=tk.NORMAL)
        self._date_entry.config(state="normal")
        self.config(cursor="")
        if self._loading_after_id:
            self.after_cancel(self._loading_after_id)
            self._loading_after_id = None

    def _animate_loading(self):
        frames = ["Carregando.", "Carregando..", "Carregando..."]
        self._loading_idx = (getattr(self, "_loading_idx", -1) + 1) % len(frames)
        self._set_status(frames[self._loading_idx], "⏳")
        self._loading_after_id = self.after(400, self._animate_loading)

    def _ensure_tickers(self) -> list[str]:
        tickers = self._ticker_list.get_tickers()
        if not tickers:
            idiv = self._repo.get_idiv_tickers()
            if not idiv:
                return []
            self._ticker_list.set_tickers(idiv)
            tickers = idiv
        return tickers

    def _on_today(self):
        self._date_entry.set_date(date.today())
        self._on_load_data()

    def _on_load_data(self):
        self._enter_loading_state()
        ref_date = self._date_entry.get_date()
        try:
            tickers = self._ensure_tickers()
            if not tickers:
                self._set_status(
                    "Filtro vazio e não foi possível carregar a carteira IDIV.",
                    "⚠",
                )
                return
            self._tickers = tickers
            self._current_data = self._use_case.execute(ref_date, self._tickers or None)
            self._tickers = list(self._current_data.keys())
            self._all_tickers = list(self._tickers)
            self._ticker_list.set_tickers(self._tickers)
            self._ticker_combo["values"] = self._tickers
            self._ticker_list.set_counter(f"Tickers ({len(self._tickers)})")
            self._date_label.config(text=f"Dados: {ref_date}")
            self._update_charts()
            n = len(self._tickers)
            self._set_status(
                f"{n} ticker{'s' if n != 1 else ''} carregado{'s' if n != 1 else ''} para {ref_date}.",
                "✓",
            )
            self.title(f"FlowScope — {ref_date} — {n} ativos")
        except Exception as e:
            self._set_status(f"Não foi possível carregar os dados. {e}", "⚠")
        finally:
            self._exit_loading_state()

    def _on_tab_changed(self, event=None):
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab == "Análise Geral":
                sub_tab = self._general_notebook.tab(self._general_notebook.select(), "text")
            else:
                sub_tab = self._ticker_notebook.tab(self._ticker_notebook.select(), "text")
        except Exception:
            return

        content = self._tab_content.get((main_tab, sub_tab))
        if content:
            self._orientation_panel.set_content(*content)

        self._prefs["last_tab"] = main_tab
        self._prefs["last_subtab"] = sub_tab

    def _on_ticker_dir_changed(self, directory: Path) -> None:
        self._prefs["last_ticker_dir"] = str(directory)
        save_preferences(self._prefs)

    def _on_ticker_edit(self):
        tickers = self._ticker_list.get_tickers()
        if not tickers:
            idiv = self._repo.get_idiv_tickers()
            if idiv:
                self._ticker_list.set_tickers(idiv)
            else:
                self._flash_status("Não foi possível carregar a carteira IDIV.", "⚠")
                return
        self._ticker_combo["values"] = tickers
        self._update_charts()
        self._update_ticker_counter()
        self._update_title()
        self._flash_status("Filtro aplicado!", "ℹ")

    def _on_date_change(self):
        ref_date = self._date_entry.get_date()
        self._current_data = self._use_case.execute(ref_date, self._tickers or None)
        self._tickers = list(self._current_data.keys())
        self._all_tickers = list(self._tickers)
        self._ticker_list.set_tickers(self._tickers)
        self._update_charts()

    def _update_charts(self):
        import matplotlib

        matplotlib.use("TkAgg")

        tickers = self._ticker_list.get_tickers()
        filtered = {t: self._current_data.get(t) for t in tickers if t in self._current_data}
        self._vwap_chart.update(filtered)

    def _update_ticker_counter(self):
        filtered = self._ticker_list.get_tickers()
        active = [t for t in filtered if t in self._current_data]
        n_total = len(self._all_tickers)
        n_filtered = len(active)
        if n_filtered < n_total and n_total > 0:
            self._ticker_list.set_counter(f"Exibindo {n_filtered} de {n_total} ativos")
        elif n_total > 0:
            self._ticker_list.set_counter(f"Tickers ({n_total})")

    def _update_title(self):
        filtered = self._ticker_list.get_tickers()
        active = [t for t in filtered if t in self._current_data]
        n_total = len(self._all_tickers)
        n_filtered = len(active)
        ref_date = self._date_entry.get_date()
        if n_filtered < n_total and n_total > 0:
            self.title(f"{TITLE_PREFIX} — {ref_date} — {n_filtered} de {n_total} ativos")
        elif n_total > 0:
            self.title(f"{TITLE_PREFIX} — {ref_date} — {n_total} ativos")
        else:
            self.title(TITLE_PREFIX)

    def _copy_data(self):
        try:
            import pyxclip
            import pyxclip.main as pyxclip_main

            lines = ["Ticker;VWAP;CVD"]
            for ticker, data in self._current_data.items():
                vwap = data.get("vwap", {}).get("period_vwap", "")
                cvd = data.get("cvd", {}).get("accumulated_cvd", "")
                lines.append(f"{ticker};{vwap};{cvd}")
            text = "\n".join(lines)
            pyxclip_main.copy(text)
            self._flash_status("Dados copiados!")
        except Exception:
            self._fallback_clipboard_text()

    def _fallback_clipboard_text(self):
        self.clipboard_clear()
        lines = ["Ticker;VWAP;CVD"]
        for ticker, data in self._current_data.items():
            vwap = data.get("vwap", {}).get("period_vwap", "")
            cvd = data.get("cvd", {}).get("accumulated_cvd", "")
            lines.append(f"{ticker};{vwap};{cvd}")
        self.clipboard_append("\n".join(lines))
        self._flash_status("Dados copiados! (fallback)")

    def _copy_chart(self):
        from flowscope.infrastructure.clipboard_image import ClipboardError, copy_image_to_clipboard

        figure = self._vwap_chart.get_figure()
        if figure is not None:
            try:
                copy_image_to_clipboard(figure)
                self._flash_status("Gráfico copiado!")
            except ClipboardError as e:
                self._set_status(f"Erro: {e}", "⚠")

    def _bind_shortcuts(self):
        self._date_entry.bind("<Return>", lambda e: self._on_load_data())
        self.bind_all("<Control-c>", lambda e: self._copy_data())
        self.bind_all("<F5>", lambda e: self._on_load_data())

    def _on_close(self):
        self._prefs["window_geometry"] = self.geometry()
        self._prefs["last_date"] = str(self._date_entry.get_date())
        self._prefs["last_tab"] = self._prefs.get("last_tab", "Análise Geral")
        self._prefs["last_subtab"] = self._prefs.get("last_subtab", "VWAP")
        try:
            pos0 = self._main_pw.sash_coord(0) if hasattr(self, "_main_pw") else None
            self._prefs["sash_positions"] = list(pos0) if pos0 else None
        except Exception:
            pass
        save_preferences(self._prefs)
        self.destroy()
