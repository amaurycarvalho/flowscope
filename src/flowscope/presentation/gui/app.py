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
from flowscope.presentation.gui.charts.cvd_hist import CVDHistChart
from flowscope.presentation.gui.charts.scatter import ScatterChart
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart
from flowscope.presentation.gui.widgets.analysis_text import AnalysisText
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
    "last_chart": "vwap",
    "window_geometry": None,
    "sash_positions": None,
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

        selector_frame = ttk.LabelFrame(left_pw, text="Visualização")
        left_pw.add(selector_frame, stretch="never")
        self._chart_var = tk.StringVar(value=self._prefs.get("last_chart", "vwap"))
        tooltips = {
            "VWAP": "Preço médio ponderado pela quantidade de ativos negociados. Mostra distribuição de preços no período.",
            "CVD": "Cumulative Volume Delta",
            "Dispersão": "Correlação entre VWAP e CVD",
        }
        for text, value in [("VWAP", "vwap"), ("CVD", "cvd"), ("Dispersão", "scatter")]:
            rb = tk.Radiobutton(
                selector_frame,
                text=text,
                variable=self._chart_var,
                value=value,
                command=self._on_chart_select,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=PAD_SMALL)
            ToolTip(rb, tooltips[text])

        self._chart_container = tk.Frame(left_pw)
        left_pw.add(self._chart_container, stretch="always")

        self._chart_title_var = tk.StringVar(value="VWAP — Distribuição de Preços")
        self._chart_title = tk.Label(
            self._chart_container,
            textvariable=self._chart_title_var,
            font=("TkDefaultFont", 10, "bold"),
        )
        self._chart_title.pack(anchor=tk.W)

        self._empty_label = tk.Label(
            self._chart_container,
            text="Nenhum ticker corresponde ao filtro.",
            font=("TkDefaultFont", 12),
            fg="gray",
        )

        self._vwap_chart = VWAPHistChart(self._chart_container)
        self._cvd_chart = CVDHistChart(self._chart_container)
        self._scatter_chart = ScatterChart(self._chart_container)
        self._show_current_chart()

        right_pw = tk.PanedWindow(
            self._main_pw, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=6
        )
        self._main_pw.add(right_pw, stretch="never")

        ticker_frame = tk.Frame(right_pw)
        right_pw.add(ticker_frame, stretch="always")
        self._ticker_list = TickerList(ticker_frame, on_change=self._on_ticker_edit)
        self._ticker_list.frame.pack(fill=tk.BOTH, expand=True)

        analysis_frame = tk.Frame(right_pw)
        right_pw.add(analysis_frame, stretch="never")
        self._analysis_text = AnalysisText(analysis_frame)
        self._analysis_text.frame.pack(fill=tk.X)

        if self._prefs.get("sash_positions"):
            try:
                pos = self._prefs["sash_positions"]
                if isinstance(pos, (list, tuple)) and len(pos) >= 4:
                    self.after(100, lambda: self._restore_sashes(pos))
            except Exception:
                pass

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
        self._date_entry.config(state=tk.DISABLED)
        self.config(cursor="watch")
        self.update_idletasks()
        self._animate_loading()

    def _exit_loading_state(self):
        self._load_button.config(state=tk.NORMAL)
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

    def _on_chart_select(self):
        self._show_current_chart()
        self._prefs["last_chart"] = self._chart_var.get()

    def _show_current_chart(self):
        if hasattr(self, "_ticker_list"):
            tickers = self._ticker_list.get_tickers()
            filtered = {t: self._current_data.get(t) for t in tickers if t in self._current_data}
            if not filtered and self._current_data:
                self._empty_label.pack(fill=tk.BOTH, expand=True)
                for c in (self._vwap_chart, self._cvd_chart, self._scatter_chart):
                    c.frame.pack_forget()
                return
        self._empty_label.pack_forget()
        for c in (self._vwap_chart, self._cvd_chart, self._scatter_chart):
            c.frame.pack_forget()
        selected = self._chart_var.get()
        titles = {
            "vwap": "VWAP — Distribuição de Preços",
            "cvd": "CVD Histogram",
            "scatter": "VWAP × CVD — Dispersão",
        }
        self._chart_title_var.set(titles[selected])
        {
            "vwap": self._vwap_chart,
            "cvd": self._cvd_chart,
            "scatter": self._scatter_chart,
        }[selected].frame.pack(fill=tk.BOTH, expand=True)

    def _on_ticker_edit(self):
        tickers = self._ticker_list.get_tickers()
        if not tickers:
            idiv = self._repo.get_idiv_tickers()
            if idiv:
                self._ticker_list.set_tickers(idiv)
            else:
                self._flash_status("Não foi possível carregar a carteira IDIV.", "⚠")
                return
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
        self._cvd_chart.update(filtered)
        self._scatter_chart.update(filtered)
        self._show_current_chart()

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

        chart = {
            "vwap": self._vwap_chart,
            "cvd": self._cvd_chart,
            "scatter": self._scatter_chart,
        }[self._chart_var.get()]
        figure = chart.get_figure()
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
        self._prefs["last_chart"] = self._chart_var.get()
        try:
            pos0 = self._main_pw.sash_coord(0) if hasattr(self, "_main_pw") else None
            self._prefs["sash_positions"] = list(pos0) if pos0 else None
        except Exception:
            pass
        save_preferences(self._prefs)
        self.destroy()
