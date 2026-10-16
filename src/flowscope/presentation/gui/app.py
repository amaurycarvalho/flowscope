"""Interface gráfica principal do FlowScope em Tkinter."""

import json
import logging
import platform
import tkinter as tk
from datetime import date, datetime, timezone
from pathlib import Path

from flowscope.presentation.gui.app_about_actions import AboutActionsMixin
from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_constants import TITLE_PREFIX
from flowscope.presentation.gui.app_csv import CsvMixin
from flowscope.presentation.gui.app_layout import LayoutMixin
from flowscope.presentation.gui.app_resumos_actions import ResumosActionsMixin
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_wiring import WiringMixin
from flowscope.presentation.gui.noticias_actions import NoticiasActionsMixin
from flowscope.presentation.gui.startup_gate import StartupGateMixin
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
    "last_ticker_file": None,
    "fundamental_column_widths": None,
}


def _ler_preferencias_salvas() -> dict:
    """Lê do arquivo apenas as chaves de preferência conhecidas."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {chave: data[chave] for chave in DEFAULT_CONFIG if chave in data}


def _normalizar_texto(valor: object) -> str | None:
    """Devolve o texto informado ou ``None`` quando vazio ou de tipo inválido."""
    if not isinstance(valor, str) or not valor.strip():
        return None
    return valor


def _normalizar_tickers(valor: object) -> list[str] | None:
    """Devolve a lista de tickers válidos ou ``None`` quando inválida."""
    if not isinstance(valor, list):
        return None
    return [t for t in valor if isinstance(t, str) and t.strip()]


def _normalizar_largura(valor: object) -> int | None:
    """Devolve a largura como inteiro positivo ou ``None`` quando inválida."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
        return None
    return int(valor)


def load_preferences() -> dict:
    """Carrega as preferências salvas no arquivo de configuração.

    Apenas as chaves de preferência são carregadas. Blocos geridos por outros
    módulos (como ``llm``) permanecem no arquivo, mas não entram no estado da
    interface, para não serem sobrescritos ao fechar a aplicação.
    """
    prefs = dict(DEFAULT_CONFIG)
    prefs.update(_ler_preferencias_salvas())
    prefs["last_tickers"] = _normalizar_tickers(prefs.get("last_tickers"))
    prefs["last_ticker_file"] = _normalizar_texto(prefs.get("last_ticker_file"))
    prefs["sash_positions"] = _normalizar_largura(prefs.get("sash_positions"))
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


class FlowScopeGUI(WiringMixin, TabActionsMixin, TabsLayoutMixin, StatusMixin, StartupGateMixin, LayoutMixin, ActionsMixin, AboutActionsMixin, NoticiasActionsMixin, ResumosActionsMixin, CsvMixin, tk.Tk):
    """Janela principal da aplicação FlowScope."""

    def __init__(self: "FlowScopeGUI") -> None:
        """Inicializa a janela principal e seus componentes."""
        super().__init__()
        self._prefs = load_preferences()
        arquivo_salvo = self._prefs.get("last_ticker_file")
        self._watchlist_file: Path | None = (
            Path(arquivo_salvo) if arquivo_salvo else None
        )
        self._watchlist_dirty = False
        self._index_name: str | None = None
        self._update_window_title()

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
        # O escudo é colocado antes de construir os painéis para que qualquer
        # pintura da janela durante a inicialização já saia coberta; o gate o
        # reergue e o mantém até a carga inicial em background concluir.
        self.colocar_escudo()

        self._current_data: dict = {}
        self._sampling_dates: list[date] = []
        self._tickers: list[str] = []
        self._all_tickers: list[str] = []
        self._fundamental_data: dict = {}
        self._ticker_selecionado: str | None = None
        self._loading_after_id = None
        self._flash_after_id = None
        self._update_checked = False

        self._wire_ports()
        self._build_top_bar()
        self.colocar_escudo()
        self._wire_documentos()
        self._wire_noticias()
        # A barra de status é empacotada antes da área principal expansível para
        # não ser cortada pelo tamanho requisitado dos painéis (matplotlib).
        self._build_statusbar()
        self._build_main_area()
        self.colocar_escudo()
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
        self.iniciar_gate()

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

    def _update_window_title(self: "FlowScopeGUI") -> None:
        """Compõe o título com o nome do watchlist e o marcador de alteração."""
        if self._watchlist_file is not None:
            nome = self._watchlist_file.name
        elif self._index_name is not None:
            nome = self._index_name
        else:
            nome = "Nova lista.txt"
        sufixo = "*" if self._watchlist_dirty else ""
        self.title(f"{TITLE_PREFIX} — {nome}{sufixo}")

    def _on_watchlist_file_changed(self: "FlowScopeGUI", path: Path) -> None:
        """Atualiza o título e persiste o caminho do arquivo carregado/salvo."""
        self._watchlist_file = Path(path)
        self._index_name = None
        self._watchlist_dirty = False
        self._prefs["last_ticker_file"] = str(self._watchlist_file)
        save_preferences(self._prefs)
        self._update_window_title()

    def _on_watchlist_content_changed(self: "FlowScopeGUI") -> None:
        """Marca o watchlist como alterado e reflete no título."""
        self._watchlist_dirty = True
        self._update_window_title()

    def _on_index_click(self: "FlowScopeGUI", index: str) -> None:
        """Exibe o nome do índice no título e submete a carga da carteira."""
        self._watchlist_file = None
        self._watchlist_dirty = False
        self._index_name = f"{index}.txt"
        self._update_window_title()
        self._controller.on_index_clicked(index)

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

    def _largura_divisor_direito(self: "FlowScopeGUI") -> int | None:
        """Retorna a largura, em pixels, do painel direito do divisor principal.

        Persistir a largura (e não a coordenada absoluta do sash) mantém o
        painel direito estável quando a aplicação reabre em outra resolução.
        """
        painel = getattr(self, "_main_pw", None)
        if painel is None:
            return None
        try:
            total = painel.winfo_width()
            x = painel.sash_coord(0)[0]
        except (tk.TclError, IndexError):
            return None
        largura = total - x
        return int(largura) if largura > 0 else None

    def _on_close(self: "FlowScopeGUI") -> None:
        self._prefs["window_geometry"] = self.geometry()
        self._prefs["last_date"] = str(self._date_entry.get_date())
        self._prefs["last_tab"] = self._prefs.get("last_tab", "Análise Geral")
        self._prefs["last_subtab"] = self._prefs.get("last_subtab", "Fundamentos")
        self._prefs["last_tickers"] = self._ticker_list.get_all_listbox_tickers()
        if self._watchlist_file is not None:
            self._prefs["last_ticker_file"] = str(self._watchlist_file)
        if hasattr(self, "_fundamental_table"):
            self._prefs["fundamental_column_widths"] = (
                self._fundamental_table.get_column_widths()
            )
        self._prefs["sash_positions"] = self._largura_divisor_direito()
        save_preferences(self._prefs)
        self.destroy()
