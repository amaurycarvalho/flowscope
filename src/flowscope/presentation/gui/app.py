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
from flowscope.presentation.gui.progress import ProgressReporter
from flowscope.presentation.gui.charts.vwap_hist import VWAPHistChart
from flowscope.presentation.gui.charts.quadrant_chart import QuadrantChart
from flowscope.presentation.gui.charts.dominance_ranking import DominanceRankingChart
from flowscope.presentation.gui.charts.dominance_timeline import DominanceTimelineChart
from flowscope.presentation.gui.charts.price_range_panel import PriceRangePanel
from flowscope.presentation.gui.widgets.orientation_panel import OrientationPanel
from flowscope.presentation.gui.widgets.ticker_list import TickerList
from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope import __version__
from PIL import Image, ImageTk

from flowscope.presentation.main import (
    _create_desktop_shortcut,
    _desktop_shortcut_exists,
    _resolve_icon_path,
)

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
        self._charts_dirty: bool = True

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

    def _load_icon(self, filename: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
        path = _resolve_icon_path(filename)
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        if not hasattr(self, "_icon_refs"):
            self._icon_refs = []
        self._icon_refs.append(photo)
        return photo

    def _set_icon(self):
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
            top, image=self._load_icon("document-open-recent.png"),
            command=self._on_today, cursor="hand2", padx=0,
        )
        self._today_button.pack(side=tk.LEFT, padx=(0, PAD_SMALL))
        self._load_button = tk.Button(
            top, image=self._load_icon("view-refresh.png"),
            command=self._on_load_data, cursor="hand2", padx=0,
        )
        self._load_button.pack(side=tk.LEFT, padx=PAD_SMALL)

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
        ToolTip(self._copy_data_btn, "Copiar dados CSV para a área de transferência")

    def _build_main_area(self):
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

        general_vwap_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_vwap_frame, text="VWAP")
        self._vwap_chart = VWAPHistChart(general_vwap_frame, copy_chart_callback=self._copy_chart)
        self._vwap_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_quadrantes_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_quadrantes_frame, text="Quadrantes")
        self._quadrant_chart = QuadrantChart(
            general_quadrantes_frame,
            copy_chart_callback=self._copy_chart,
            summary_callback=self._on_quadrant_summary,
        )
        self._quadrant_chart.frame.pack(fill=tk.BOTH, expand=True)

        general_dominance_frame = ttk.Frame(self._general_notebook)
        self._general_notebook.add(general_dominance_frame, text="Dominância do Pregão")
        self._dominance_ranking = DominanceRankingChart(
            general_dominance_frame, copy_chart_callback=self._copy_chart,
        )
        self._dominance_ranking.frame.pack(fill=tk.BOTH, expand=True)

        ticker_main_frame = ttk.Frame(self._main_notebook)
        self._main_notebook.add(ticker_main_frame, text="Análise do Ticker")

        self._ticker_notebook = ttk.Notebook(ticker_main_frame)
        self._ticker_notebook.pack(fill=tk.BOTH, expand=True)

        tab_configs = [
            ("Evolução da Dominância", "clv", "daily_efficiency", "dominance_score", "daily_money_flow"),
            ("Amplitude de Preço", "range", "range_percentual", "typical_price", "median_price", "weighted_close"),
            ("Fluxo Financeiro", "clv", "money_flow_multiplier", "money_flow_volume", "buying_pressure", "selling_pressure", "vwap_distance"),
            ("Participação Institucional", "average_trade_size", "average_financial_ticket"),
            ("Eficiência do Movimento", "daily_efficiency"),
            ("Resumo Geral", None),
        ]
        self._ticker_indicator_frames = {}
        enabled_tabs = {"Evolução da Dominância", "Amplitude de Preço"}
        for name, *keys in tab_configs:
            frame = ttk.Frame(self._ticker_notebook)
            kwargs = {"text": name}
            if name not in enabled_tabs:
                kwargs["state"] = "disabled"
            self._ticker_notebook.add(frame, **kwargs)
            if name == "Evolução da Dominância":
                self._dominance_timeline = DominanceTimelineChart(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._dominance_timeline.frame.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": None, "keys": keys}
            elif name == "Amplitude de Preço":
                self._price_range_panel = PriceRangePanel(
                    frame, copy_chart_callback=self._copy_chart,
                )
                self._price_range_panel.frame.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": None, "keys": keys}
            else:
                text_widget = tk.Text(frame, wrap=tk.WORD, font=("TkDefaultFont", 11),
                                      padx=8, pady=8, relief=tk.FLAT, state=tk.DISABLED)
                text_widget.pack(fill=tk.BOTH, expand=True)
                self._ticker_indicator_frames[name] = {"frame": frame, "text": text_widget, "keys": keys}

        self._tab_content = {
            ("Análise Geral", "VWAP"): (
                "VWAP — Volume Weighted Average Price",
                [
                    ("Objetivo: ", "bold"),
                    ("Identificar o preço médio ponderado pelo volume negociado no período, revelando o valor justo da ação sob a ótica do fluxo de ordens.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Quem está acima do preço justo e quem está abaixo?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("VWAP (preço médio ponderado), volume por bucket de preço (volume profile), preço de fechamento (LastPric), preço mínimo e máximo (MinPric, MaxPric).\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("O VWAP é a referência de preço justo do período. Negociações acima do VWAP indicam viés comprador; abaixo, viés vendedor. "
                     "A largura do violino mostra em quais faixas de preço houve maior concentração de volume. "
                     "O último preço (losango vermelho) em relação ao VWAP indica se o fechamento reforça ou contradiz a tendência do período.", ""),
                ]
            ),
            ("Análise Geral", "Quadrantes"): (
                "Quadrantes — CLV vs VWAP Distance",
                [
                    ("Objetivo: ", "bold"),
                    ("Classificar ativos em quatro quadrantes com base no CLV (eixo X) e no desvio do VWAP (eixo Y), "
                     "revelando a interação entre fluxo comprador/vendedor e posição relativa ao preço justo.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Quem dominou o fechamento? O preço terminou acima ou abaixo do valor justo? Quanto volume financeiro sustentou esse comportamento?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("CLV (Close Location Value), VWAP Distance (desvio percentual do último preço "
                     "em relação ao VWAP diário), Volume (FinInstrmQty como tamanho da bolha).\n\n", ""),
                    ("Como interpretar:\n", "bold"),
                    ("• Q1 (CLV > 0, acima do VWAP): compra forte confirmada — fechamento na metade superior do range e acima do VWAP.\n"
                     "• Q2 (CLV < 0, acima do VWAP): venda relativa — ativo acima do VWAP mas perdeu força no fechamento (possível realização).\n"
                     "• Q3 (CLV < 0, abaixo do VWAP): venda forte confirmada — vendedores dominaram o dia.\n"
                     "• Q4 (CLV > 0, abaixo do VWAP): compra em desconto — reação compradora insuficiente para recuperar o VWAP.\n\n"
                     "As setas cinzas mostram a trajetória dos dias anteriores, evidenciando a evolução temporal de cada ativo.", ""),
                ]
            ),
            ("Análise Geral", "Dominância do Pregão"): (
                "Dominância do Pregão — Ranking de Tickers por CLV",
                [
                    ("Objetivo: ", "bold"),
                    ("Visualizar rapidamente quais ativos tiveram dominância compradora ou vendedora no último pregão.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Quem venceu a disputa diária pelo preço?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("CLV (Close Location Value) para direção/intensidade, Money Flow Volume (MFV) para capital envolvido.\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("Barras para a direita indicam dominância compradora (CLV positivo); para a esquerda, vendedora (CLV negativo). "
                     "Quanto maior o comprimento, mais intensa a dominância. O traço horizontal sobre a barra representa o volume financeiro que sustentou o movimento. "
                     "Passe o mouse sobre as barras para ver detalhes do ticker.", ""),
                ]
            ),
            ("Análise do Ticker", "Evolução da Dominância"): (
                "Evolução da Dominância — Histórico de CLV por Pregão",
                [
                    ("Objetivo: ", "bold"),
                    ("Visualizar a evolução temporal da dominância compradora/vendedora para o ticker selecionado.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Quem venceu a disputa diária pelo preço?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("CLV (Close Location Value) nas barras, Daily Money Flow (traço horizontal sobre a barra).\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("Cada barra representa um pregão. Direita = compradores dominaram; Esquerda = vendedores dominaram. "
                     "O traço horizontal indica o fluxo financeiro diário. Passe o mouse sobre as barras para ver detalhes da dominância e convicção do movimento.", ""),
                ]
            ),
            ("Análise do Ticker", "Amplitude de Preço"): (
                "Amplitude de Preço — Painel Visual",
                [
                    ("Objetivo: ", "bold"),
                    ("Analisar se o preço apenas oscilou ou houve um movimento direcional convincente durante o pregão, "
                     "mostrando como a posição do fechamento dentro do range evoluiu nos últimos dias.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Onde o preço andou (trajetória)? Quanto andou (amplitude)? Andou com convicção (eficiência)?\"\n\n", "italic"),
                    ("Indicadores envolvidos:\n", "bold"),
                    ("• Trajetória: onde o preço se posicionou dentro da faixa do dia (0%=perto do preço mínimo, "
                     "100%=perto do preço máximo), acompanhado dos marcadores ● (preço de fechamento, no tamanho da amplitude), "
                     "M (Median), T (Typical), V (VWAP) e W (Weighted Close);\n"
                     "• Amplitude: quanto o preço oscilou, em percentual do preço médio (pequeno=pouco, grande=muito);\n"
                     "• Eficiência: o movimento teve convicção ou foi ruído (0%=muito ruído, 100%=muita convicção);\n"
                     "• CLV: Close Location Value, indicando pressão vendedora (negativo) ou compradora (positivo);\n"
                     "• Classificação do pregão: \"Pregão Lateral\" (Amplitude Relativa ≤ mediana histórica e Eficiência ≤ 0,30), "
                     "\"Volatilidade sem Direção\" (Amplitude Relativa > mediana e Eficiência ≤ 0,30), "
                     "\"Movimento Consistente\" (Amplitude Relativa ≤ mediana e Eficiência > 0,30) e "
                     "\"Movimento Direcional Forte\" (Amplitude Relativa > mediana e Eficiência > 0,30).\n\n", ""),
                     ("Como interpretar: ", "bold"),
                     ("Uma Amplitude elevada indica maior volatilidade, mas não significa necessariamente uma tendência forte. "
                      "A Eficiência elevada mostra que a oscilação foi convertida em avanço efetivo, sugerindo convicção. "
                      "Um CLV próximo de +1 indica fechamento perto da máxima (pressão compradora); próximo de -1, perto da mínima "
                      "(pressão vendedora). Dias com barra de fundo verde consecutiva = sequência direcional forte.\n\n"
                      "Classificações:\n"
                      "• \"Pregão Lateral\": amplitude baixa e eficiência baixa — o preço andou pouco e sem convicção. "
                      "Indecisão total, mercado sem direção.\n"
                      "• \"Volatilidade sem Direção\": amplitude alta e eficiência baixa — o preço oscilou muito mas sem rumo. "
                      "Mercado nervoso, barulho sem sinal direcional.\n"
                      "• \"Movimento Consistente\": amplitude baixa e eficiência alta — movimento eficiente com pouca oscilação. "
                      "Compradores ou vendedores agiram com foco e sem dispersão.\n"
                      "• \"Movimento Direcional Forte\": amplitude alta e eficiência alta — volatilidade com convicção. "
                      "Movimento forte e direcionado, indicando consenso no fluxo de ordens.\n\n"
                      "Passe o mouse sobre os marcadores para ver valores detalhados.", ""),
                ]
            ),
            ("Análise do Ticker", "Fluxo Financeiro"): (
                "Fluxo Financeiro — CLV e Money Flow",
                [
                    ("Objetivo: ", "bold"),
                    ("Medir o viés comprador ou vendedor do pregão.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"O movimento ocorreu com dinheiro ou apenas por falta de liquidez?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("CLV (Close Location Value), Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure.\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("CLV varia de -1 (fechamento na mínima) a +1 (fechamento na máxima). Money Flow Volume = CLV × Volume Financeiro, "
                     "acumulado no período. Positivo indica predomínio comprador; negativo, vendedor. Buying + Selling Pressure = 1.", ""),
                ]
            ),
            ("Análise do Ticker", "Participação Institucional"): (
                "Participação Institucional — Tamanho dos Negócios",
                [
                    ("Objetivo: ", "bold"),
                    ("Estimar o perfil dos participantes com base no tamanho médio das negociações.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"Quem parece estar negociando? Grandes participantes ou varejo?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("Average Trade Size (ações por negócio), Average Financial Ticket (valor por negócio).\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("Tickets médios mais altos sugerem participação institucional (grandes blocos). Tickets baixos sugerem "
                     "predomínio de pessoa física. Acompanhar a evolução ao longo dos dias revela mudanças na composição do fluxo.", ""),
                ]
            ),
            ("Análise do Ticker", "Eficiência do Movimento"): (
                "Eficiência do Movimento",
                [
                    ("Objetivo: ", "bold"),
                    ("Medir quanto do range diário resultou em deslocamento efetivo do preço.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"O mercado caminhou com convicção ou apenas oscilou?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("Daily Efficiency = |Fechamento − Preço Médio| / Range.\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("Próximo de 0 → pregão lateral (preço andou mas voltou). Próximo de 1 → movimento direcional "
                     "(o range inteiro resultou em deslocamento). Valores baixos indicam indecisão; altos, convicção.", ""),
                ]
            ),
            ("Análise do Ticker", "Resumo Geral"): (
                "Resumo Geral — Todos os Indicadores",
                [
                    ("Objetivo: ", "bold"),
                    ("Consolidar todos os indicadores do ticker em uma única visualização.\n\n", ""),
                    ("Responde a pergunta: ", "bold"),
                    ("\"O que realmente aconteceu neste ativo?\"\n\n", "italic"),
                    ("Indicadores envolvidos: ", "bold"),
                    ("Range, Range%, Typical Price, Median Price, Weighted Close, CLV, "
                     "Money Flow Multiplier, Money Flow Volume, Buying/Selling Pressure, Average Trade Size, "
                     "Average Financial Ticket, Daily Efficiency, Financial Density, Trade Density, Volume Density.\n\n", ""),
                    ("Como interpretar: ", "bold"),
                    ("Use este painel para uma visão panorâmica de todos os indicadores disponíveis "
                     "para o ticker selecionado.", ""),
                ]
            ),
        }

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
            on_change=self._on_ticker_edit,
            on_load=self._on_load_data,
            initialdir=self._prefs.get("last_ticker_dir"),
            on_dir_changed=self._on_ticker_dir_changed,
            on_data_needed=self._on_load_data,
            on_index_click={
                "IBOV": lambda: self._fill_with_index("IBOV") or self._on_load_data(),
                "IDIV": lambda: self._fill_with_index("IDIV") or self._on_load_data(),
                "IFIX": lambda: self._fill_with_index("IFIX") or self._on_load_data(),
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
            if len(positions) >= 4 and hasattr(self, "_left_pw"):
                self._left_pw.sash_place(0, 0, positions[1])
        except Exception:
            pass

    def _build_action_buttons(self):
        pass

    def _build_statusbar(self):
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

    def _set_status(self, msg: str, icon: str = "") -> None:
        text = f"{icon} {msg}" if icon else msg
        self._status_var.set(text)
        self._progress_bar.pack_forget()

    def _set_progress(self, current: int, total: int, label: str) -> None:
        pct = int(current / max(total, 1) * 100) if total > 0 else 100
        self._status_var.set(label)
        self._progress_bar["value"] = pct
        self._progress_bar.pack(side=tk.RIGHT, padx=PAD_SMALL)
        self.update_idletasks()

    def _flash_status(self, msg: str, icon: str = "✓", clear_ms: int = 2500) -> None:
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
        self._set_status(msg, icon)
        self._flash_after_id = self.after(clear_ms, lambda: self._set_status("Pronto."))

    def _set_wait_cursor(self):
        self.config(cursor="watch")
        self.update_idletasks()

    def _clear_wait_cursor(self):
        self.config(cursor="")

    def _enter_loading_state(self):
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
            self._flash_after_id = None
        self._load_button.config(state=tk.DISABLED)
        self._today_button.config(state=tk.DISABLED)
        self._date_entry.config(state=tk.DISABLED)
        self._set_wait_cursor()

    def _exit_loading_state(self):
        self._load_button.config(state=tk.NORMAL)
        self._today_button.config(state=tk.NORMAL)
        self._date_entry.config(state="normal")
        self._clear_wait_cursor()
        self._progress_bar.pack_forget()
        self._progress_bar["value"] = 0

    def _fill_with_index(self, index: str, reporter: ProgressReporter | None = None) -> None:
        if reporter:
            reporter.start_phase(f"Baixando portfólio {index}...", total=1, weight=1)
            self._set_progress(0, 1, f"Baixando portfólio {index}...")
        else:
            self._set_status(f"Baixando portfólio {index}...", "⏳")
            self.update_idletasks()

        def _portfolio_cb(detail: str, failed: bool) -> None:
            if reporter and not failed:
                reporter.advance(1, detail)

        tickers = self._repo.get_index_tickers(index, progress_callback=_portfolio_cb)
        if tickers:
            self._ticker_list.set_tickers(tickers)
            if reporter:
                reporter.finish_phase()
            self._flash_status(f"Carteira {index} carregada com {len(tickers)} ativos.")
        else:
            if reporter:
                reporter.finish_phase()
            self._flash_status(f"Não foi possível carregar a carteira {index}.", "⚠")

    def _ensure_tickers(self, reporter: ProgressReporter | None = None) -> list[str]:
        tickers = self._ticker_list.get_all_listbox_tickers()
        if not tickers:
            self._fill_with_index("IDIV", reporter=reporter)
            tickers = self._ticker_list.get_all_listbox_tickers()
        return tickers

    def _on_today(self):
        self._date_entry.set_date(date.today())
        self._on_load_data()

    def _on_load_data(self):
        self._enter_loading_state()
        ref_date = self._date_entry.get_date()
        reporter = ProgressReporter(on_update=self._set_progress)
        try:
            tickers = self._ensure_tickers(reporter=reporter)
            if not tickers:
                self._set_status(
                    "Filtro vazio e não foi possível carregar a carteira IDIV.",
                    "⚠",
                )
                return
            self._tickers = list(tickers)
            dates = self._repo.get_available_dates(ref_date)

            def _pipeline_cb(detail: str, failed: bool) -> None:
                if failed:
                    reporter.fail(1, detail)
                else:
                    reporter.advance(1, detail)

            reporter.start_phase("Baixando dados históricos", total=len(dates), weight=3)
            self._current_data = self._use_case.execute(
                ref_date, self._tickers or None,
                progress_callback=_pipeline_cb,
            )
            reporter.finish_phase()
            reporter.start_phase("Processando indicadores", total=1, weight=2)
            reporter.finish_phase()
            self._ticker_list.set_counter(f"Tickers ({len(self._tickers)})")
            self._date_label.config(text=f"Dados: {ref_date}")
            self._charts_dirty = True
            self._refresh_current_tab()
            n = len(self._tickers)
            self._copy_data_btn.config(state=tk.NORMAL)
            self._set_status(
                f"{n} ticker{'s' if n != 1 else ''} carregado{'s' if n != 1 else ''} para {ref_date}.",
                "✓",
            )
        except Exception as e:
            self._set_status(f"Não foi possível carregar os dados. {e}", "⚠")
        finally:
            self._exit_loading_state()

    def _get_selected_ticker(self) -> str | None:
        selected = self._ticker_list.get_tickers()
        if selected:
            return selected[0]
        all_tickers = self._ticker_list.get_all_listbox_tickers()
        if all_tickers:
            return all_tickers[0]
        return None

    def _update_ticker_indicator_tabs(self):
        ticker = self._get_selected_ticker()
        data = self._current_data.get(ticker) if ticker else None
        for name, info in self._ticker_indicator_frames.items():
            if name == "Evolução da Dominância":
                if hasattr(self, "_dominance_timeline"):
                    self._dominance_timeline.update(self._current_data, ticker=ticker)
                continue
            if name == "Amplitude de Preço":
                if hasattr(self, "_price_range_panel"):
                    self._price_range_panel.update(self._current_data, ticker=ticker)
                continue
            text_w = info["text"]
            text_w.config(state=tk.NORMAL)
            text_w.delete("1.0", tk.END)
            if not data:
                text_w.insert(tk.END, "Selecione um ticker e carregue os dados.")
                text_w.config(state=tk.DISABLED)
                continue
            if info["keys"][0] is None:
                self._format_all_indicators(text_w, ticker, data)
            else:
                self._format_selected_indicators(text_w, ticker, data, info["keys"])
            text_w.config(state=tk.DISABLED)

    def _format_selected_indicators(self, text_w, ticker, data, keys):
        all_inds = data.get("all_indicators", {})
        for key in keys:
            val = all_inds.get(key, {}).get(ticker) if isinstance(all_inds.get(key), dict) else all_inds.get(key)
            label = key.replace("_", " ").title()
            if val is None:
                text_w.insert(tk.END, f"{label}: --\n")
            elif isinstance(val, dict):
                if val:
                    last_date = max(val.keys())
                    display = val[last_date]
                    if display is None:
                        text_w.insert(tk.END, f"{label}: --\n")
                    else:
                        text_w.insert(tk.END, f"{label} ({last_date}): {display}\n")
                else:
                    text_w.insert(tk.END, f"{label}: (sem dados)\n")
            else:
                text_w.insert(tk.END, f"{label}: {val}\n")

    def _format_all_indicators(self, text_w, ticker, data):
        all_inds = data.get("all_indicators", {})
        indicators = []
        for key in ("range", "range_percentual", "typical_price", "median_price",
                     "weighted_close", "clv", "money_flow_multiplier",
                     "money_flow_volume", "buying_pressure", "selling_pressure",
                     "average_trade_size", "average_financial_ticket",
            "daily_efficiency", "dominance_score", "financial_density", "trade_density",
            "volume_density", "vwap_distance"):
            val = all_inds.get(key)
            label = key.replace("_", " ").title()
            if val is None:
                indicators.append(f"{label}: --")
            elif isinstance(val, dict):
                if val:
                    last_date = max(val.keys())
                    display = val[last_date]
                    indicators.append(f"{label}: {display if display is not None else '--'}")
                else:
                    indicators.append(f"{label}: (sem dados)")
            else:
                indicators.append(f"{label}: {val}")
        text_w.insert(tk.END, "\n".join(indicators) + "\n")
        vwap_val = data.get("vwap", {}).get("period_vwap") if data.get("vwap") else None
        mfv = data.get("money_flow_volume")
        if vwap_val is not None:
            text_w.insert(tk.END, f"\nVwap Periodo: {vwap_val}")
        if mfv is not None:
            text_w.insert(tk.END, f"\nMoney Flow Volume (acum.): {mfv}")

    def _refresh_current_tab(self):
        if not self._charts_dirty or not self._current_data:
            return
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
        except Exception:
            return
        if main_tab == "Análise Geral":
            self._update_charts()
        else:
            self._update_ticker_indicator_tabs()
        self._update_ticker_counter()
        self._charts_dirty = False

    def _on_tab_changed(self, event=None):
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            if main_tab == "Análise Geral":
                sub_tab = self._general_notebook.tab(self._general_notebook.select(), "text")
            else:
                sub_tab = self._ticker_notebook.tab(self._ticker_notebook.select(), "text")
        except Exception:
            return

        if self._current_data:
            if main_tab == "Análise Geral":
                self._update_charts()
                self._update_ticker_counter()
            else:
                self._update_ticker_indicator_tabs()
                self._update_ticker_counter()
            self._charts_dirty = False

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
            self._fill_with_index("IDIV")
            tickers = self._ticker_list.get_tickers()
            if not tickers:
                self._flash_status("Não foi possível carregar a carteira IDIV.", "⚠")
                return
        self._tickers = list(tickers)
        self._charts_dirty = True
        self._set_wait_cursor()
        try:
            self._refresh_current_tab()
        finally:
            self._clear_wait_cursor()
        self._flash_status("Filtro aplicado!", "ℹ")

    def _on_date_change(self):
        ref_date = self._date_entry.get_date()
        self._current_data = self._use_case.execute(ref_date, self._tickers or None)
        self._charts_dirty = True
        self._refresh_current_tab()

    def _on_quadrant_summary(self, summary: str) -> None:
        try:
            main_tab = self._main_notebook.tab(self._main_notebook.select(), "text")
            sub_tab = self._general_notebook.tab(self._general_notebook.select(), "text")
            if main_tab == "Análise Geral" and sub_tab == "Quadrantes":
                body = self._tab_content.get(("Análise Geral", "Quadrantes"), ("", []))[1]
                self._orientation_panel.set_content(
                    "Quadrantes — CLV vs VWAP Distance",
                    body + [("\n\n---\n\n" + summary, "")],
                )
        except Exception:
            pass

    def _update_charts(self):
        import matplotlib

        matplotlib.use("TkAgg")

        tickers = self._ticker_list.get_tickers()
        filtered = {t: self._current_data.get(t) for t in tickers if t in self._current_data}

        self._vwap_chart.update(filtered)

        show_arrows = len(filtered) == 1
        self._quadrant_chart.update(filtered, show_arrows=show_arrows)

        self._dominance_ranking.update(filtered)

    def _update_ticker_counter(self):
        all_listbox = self._ticker_list.get_all_listbox_tickers()
        filtered = self._ticker_list.get_tickers()
        active = [t for t in filtered if t in self._current_data]
        n_total = len(all_listbox)
        n_filtered = len(active)
        if n_filtered < n_total and n_total > 0:
            self._ticker_list.set_counter(f"Exibindo {n_filtered} de {n_total} ativos")
        elif n_total > 0:
            self._ticker_list.set_counter(f"Tickers ({n_total})")

    def _copy_data(self):
        try:
            import pyxclip

            lines = ["Ticker;VWAP;MoneyFlowVolume"]
            for ticker, data in self._current_data.items():
                vwap = data.get("vwap", {}).get("period_vwap", "")
                mfv = data.get("money_flow_volume", "")
                lines.append(f"{ticker};{vwap};{mfv}")
            text = "\n".join(lines)
            pyxclip.copy(text)
            self._flash_status("Dados copiados!")
        except Exception:
            self._fallback_clipboard_text()

    def _fallback_clipboard_text(self):
        self.clipboard_clear()
        lines = ["Ticker;VWAP;MoneyFlowVolume"]
        for ticker, data in self._current_data.items():
            vwap = data.get("vwap", {}).get("period_vwap", "")
            mfv = data.get("money_flow_volume", "")
            lines.append(f"{ticker};{vwap};{mfv}")
        self.clipboard_append("\n".join(lines))
        self._flash_status("Dados copiados! (fallback)")

    def _on_create_shortcut(self):
        if not platform.system() == "Linux":
            return
        if _create_desktop_shortcut():
            self._flash_status("Atalho criado!")
            if self._shortcut_btn:
                self._shortcut_btn.pack_forget()
                self._shortcut_btn = None
        else:
            self._set_status("Erro ao criar atalho.", "⚠")

    def _copy_chart(self, figure):
        from flowscope.infrastructure.clipboard_image import ClipboardError, copy_image_to_clipboard

        self._set_wait_cursor()
        try:
            copy_image_to_clipboard(figure)
            self._flash_status("Gráfico copiado!")
        except ClipboardError as e:
            self._set_status(f"Erro: {e}", "⚠")
        finally:
            self._clear_wait_cursor()

    def _bind_shortcuts(self):
        self._date_entry.bind("<Return>", lambda e: self._on_load_data())
        self.bind_all("<Control-Shift-c>", lambda e: self._copy_data())
        self.bind_all("<F5>", lambda e: self._on_load_data())

    def _on_close(self):
        self._prefs["window_geometry"] = self.geometry()
        self._prefs["last_date"] = str(self._date_entry.get_date())
        self._prefs["last_tab"] = self._prefs.get("last_tab", "Análise Geral")
        self._prefs["last_subtab"] = self._prefs.get("last_subtab", "VWAP")
        try:
            positions = []
            if hasattr(self, "_main_pw"):
                pos = self._main_pw.sash_coord(0)
                positions.extend([pos[0], pos[1]])
            if hasattr(self, "_left_pw"):
                pos = self._left_pw.sash_coord(0)
                positions.extend([pos[0], pos[1]])
            self._prefs["sash_positions"] = positions if positions else None
        except Exception:
            pass
        save_preferences(self._prefs)
        self.destroy()
