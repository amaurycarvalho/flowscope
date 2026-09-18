"""Interface gráfica principal do FlowScope em Tkinter."""

import json
import logging
import platform
import tkinter as tk
from datetime import date, datetime, timezone
from pathlib import Path

from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_constants import TITLE_PREFIX
from flowscope.presentation.gui.app_csv import CsvMixin
from flowscope.presentation.gui.app_layout import LayoutMixin
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_wiring import WiringMixin
from flowscope.presentation.main import _create_desktop_shortcut

CONFIG_DIR = Path.home() / ".flowscope"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "last_date": None,
    "last_tab": "Análise Geral",
    "last_subtab": "VWAP",
    "window_geometry": None,
    "sash_positions": None,
    "last_ticker_dir": None,
    "last_tickers": None,
    "fundamental_column_widths": None,
}


def load_preferences() -> dict:
    """Carrega as preferências salvas no arquivo de configuração.

    Apenas as chaves de preferência são carregadas. Blocos geridos por outros
    módulos (como ``llm``) permanecem no arquivo, mas não entram no estado da
    interface, para não serem sobrescritos ao fechar a aplicação.
    """
    prefs = dict(DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                prefs.update(
                    {
                        chave: data[chave]
                        for chave in DEFAULT_CONFIG
                        if chave in data
                    }
                )
    except (json.JSONDecodeError, OSError):
        pass
    last_tickers = prefs.get("last_tickers")
    if not isinstance(last_tickers, list):
        prefs["last_tickers"] = None
    else:
        prefs["last_tickers"] = [t for t in last_tickers if isinstance(t, str) and t.strip()]
    if not isinstance(prefs.get("fundamental_column_widths"), dict):
        prefs["fundamental_column_widths"] = None
    return prefs


def save_preferences(data: dict) -> None:
    """Salva as preferências preservando os demais blocos do arquivo.

    A gravação é *read-modify-write*: relê o arquivo e aplica apenas as chaves
    de preferência, mantendo blocos como ``llm`` gravados por outros módulos.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        existente: dict = {}
        if CONFIG_PATH.exists():
            try:
                carregado = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                if isinstance(carregado, dict):
                    existente = carregado
            except (json.JSONDecodeError, OSError):
                existente = {}
        existente.update(data)
        CONFIG_PATH.write_text(
            json.dumps(existente, indent=2, default=str), encoding="utf-8"
        )
    except OSError:
        pass


class FlowScopeGUI(WiringMixin, TabActionsMixin, TabsLayoutMixin, StatusMixin, LayoutMixin, ActionsMixin, CsvMixin, tk.Tk):
    """Janela principal da aplicação FlowScope."""

    def __init__(self: "FlowScopeGUI") -> None:
        """Inicializa a janela principal e seus componentes."""
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

        self._current_data: dict = {}
        self._sampling_dates: list[date] = []
        self._tickers: list[str] = []
        self._all_tickers: list[str] = []
        self._fundamental_data: dict = {}
        self._ticker_selecionado: str | None = None
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
                    datetime.strptime(self._prefs["last_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc).date()
                )
            except (ValueError, TypeError):
                pass

        last_tickers = self._prefs.get("last_tickers") or []
        if last_tickers:
            self._ticker_list.set_tickers(list(last_tickers))
            self._update_ticker_counter()

        self._wire_controller()

        self._date_entry.focus_set()
        self._set_status("Pronto. Selecione uma data e clique em Carregar.")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def report_callback_exception(
        self: "FlowScopeGUI",
        exc: type[BaseException],
        val: BaseException,
        tb: object,
    ) -> None:
        """Registra no log exceções não tratadas em callbacks do Tk."""
        logging.getLogger("flowscope").error(
            "Exceção não tratada em callback da interface",
            exc_info=(exc, val, tb),
        )

    def _build_action_buttons(self: "FlowScopeGUI") -> None:
        pass

    def _on_ticker_dir_changed(self: "FlowScopeGUI", directory: Path) -> None:
        self._prefs["last_ticker_dir"] = str(directory)
        self._prefs["last_tickers"] = self._ticker_list.get_all_listbox_tickers()
        save_preferences(self._prefs)

    def _on_create_shortcut(self: "FlowScopeGUI") -> None:
        if platform.system() != "Linux":
            return
        if _create_desktop_shortcut():
            self._flash_status("Atalho criado!")
            if self._shortcut_btn:
                self._shortcut_btn.pack_forget()
                self._shortcut_btn = None
        else:
            self._set_status("Erro ao criar atalho.", "⚠")

    def _on_close(self: "FlowScopeGUI") -> None:
        self._prefs["window_geometry"] = self.geometry()
        self._prefs["last_date"] = str(self._date_entry.get_date())
        self._prefs["last_tab"] = self._prefs.get("last_tab", "Análise Geral")
        self._prefs["last_subtab"] = self._prefs.get("last_subtab", "Fundamentos")
        self._prefs["last_tickers"] = self._ticker_list.get_all_listbox_tickers()
        if hasattr(self, "_fundamental_table"):
            self._prefs["fundamental_column_widths"] = (
                self._fundamental_table.get_column_widths()
            )
        try:
            positions = []
            if hasattr(self, "_main_pw"):
                pos = self._main_pw.sash_coord(0)
                positions.extend([pos[0], pos[1]])
            if hasattr(self, "_left_pw"):
                pos = self._left_pw.sash_coord(0)
                positions.extend([pos[0], pos[1]])
            self._prefs["sash_positions"] = positions if positions else None
        except (tk.TclError, IndexError):
            pass
        save_preferences(self._prefs)
        self.destroy()
