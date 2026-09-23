import sys
from contextlib import contextmanager

from flowscope.presentation.gui.app_csv import CsvMixin


class _BusyPresenter:
    """Registra as entradas e saídas do estado ocupado."""

    def __init__(self):
        self.entradas = 0
        self.saidas = 0

    @contextmanager
    def busy(self):
        self.entradas += 1
        try:
            yield
        finally:
            self.saidas += 1


class _TickerList:
    def __init__(self, tickers):
        self._tickers = list(tickers)

    def get_tickers(self):
        return list(self._tickers)


class _Host(CsvMixin):
    def __init__(self, tabs, tickers, fundamental):
        self._tabs = tabs
        self._ticker_list = _TickerList(tickers)
        self._fundamental_data = fundamental
        self._presenter = _BusyPresenter()
        self.status: list[str] = []
        self.clipboard: list[str] = []

    def _current_tabs(self):
        return self._tabs

    def _ticker_apresentado(self):
        return getattr(self, "_ticker_selecionado", None)

    def _flash_status(self, msg, icon=""):
        self.status.append(msg)

    def clipboard_clear(self):
        self.clipboard = []

    def clipboard_append(self, text):
        self.clipboard.append(text)


def _host(tabs=("Análise Geral", "Fundamentos"), tickers=("HGBS11", "PETR4")):
    return _Host(
        tabs,
        tickers,
        {"HGBS11": {"daily_data": []}, "PETR4": {"daily_data": []}},
    )


class TestBuildFundamentalCsv:
    def test_inclui_cabecalho_e_tickers_filtrados(self):
        host = _host()
        csv = host._build_fundamental_csv()
        linhas = csv.split("\n")
        assert linhas[0].startswith("Ticker;Nome;")
        assert [linha.split(";")[0] for linha in linhas[1:]] == ["HGBS11", "PETR4"]

    def test_csv_inclui_cabecalho_e_30_colunas(self):
        host = _host()
        linhas = host._build_fundamental_csv().split("\n")
        cabecalho = linhas[0].split(";")
        assert cabecalho[0] == "Ticker"
        assert cabecalho[1] == "Nome"
        assert len(cabecalho) == 34
        for linha in linhas[1:]:
            assert len(linha.split(";")) == 34

    def test_filtra_pelos_tickers_exibidos(self):
        host = _host(tickers=("PETR4",))
        csv = host._build_fundamental_csv()
        assert [linha.split(";")[0] for linha in csv.split("\n")[1:]] == ["PETR4"]

    def test_sem_dados_retorna_vazio_e_avisa(self):
        host = _host(tickers=())
        assert host._build_fundamental_csv() == ""
        assert host.status == ["Nenhum ticker disponível para cópia."]


class TestCsvTickers:
    def test_analise_do_ticker_usa_ticker_apresentado(self):
        host = _host(tabs=("Análise do Ticker", "Fluxo Financeiro"))
        host._ticker_selecionado = "VALE3"
        assert host._csv_tickers("Análise do Ticker") == ["VALE3"]

    def test_analise_do_ticker_sem_selecao(self):
        host = _host(tabs=("Análise do Ticker", "Fluxo Financeiro"))
        host._ticker_selecionado = None
        assert host._csv_tickers("Análise do Ticker") == []


class TestBuildCsvForCurrentTab:
    def test_fundamentos_usa_tabela(self):
        host = _host(tabs=("Análise Geral", "Fundamentos"))
        host._build_raw_csv = lambda: "RAW"
        assert host._build_csv_for_current_tab().startswith("Ticker;Nome;")

    def test_outra_sub_aba_usa_csv_bruto(self):
        host = _host(tabs=("Análise Geral", "VWAP"))
        host._build_raw_csv = lambda: "RAW"
        assert host._build_csv_for_current_tab() == "RAW"

    def test_analise_do_ticker_usa_csv_bruto(self):
        host = _host(tabs=("Análise do Ticker", "Fluxo Financeiro"))
        host._build_raw_csv = lambda: "RAW"
        assert host._build_csv_for_current_tab() == "RAW"


class TestCopyData:
    def test_fundamentos_copia_tabela_com_pyxclip(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tabs=("Análise Geral", "Fundamentos"))
        host._copy_data()
        assert copiado and copiado[0].startswith("Ticker;Nome;")
        assert host.status == ["Dados copiados!"]

    def test_outra_aba_copia_csv_bruto(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tabs=("Análise Geral", "VWAP"))
        host._build_raw_csv = lambda: "RAW"
        host._copy_data()
        assert copiado == ["RAW"]

    def test_fallback_quando_pyxclip_indisponivel(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pyxclip", None)
        host = _host(tabs=("Análise Geral", "Fundamentos"))
        host._copy_data()
        assert host.clipboard and host.clipboard[0].startswith("Ticker;Nome;")
        assert host.status == ["Dados copiados! (fallback)"]

    def test_sem_dados_nao_copia(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tickers=())
        host._copy_data()
        assert copiado == []
        assert host.status == ["Nenhum ticker disponível para cópia."]

    def test_copia_encerra_estado_ocupado_ao_final(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tabs=("Análise Geral", "Fundamentos"))
        host._copy_data()
        assert copiado
        assert host._presenter.entradas == 1
        assert host._presenter.saidas == 1


class TestCopyDocumentos:
    def test_documentos_copia_texto_do_painel(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tabs=("Análise do Ticker", "Documentos"))
        host._documents_panel = type(
            "P", (), {"texto_atual": lambda self: "texto do campo"}
        )()
        host._copy_data()
        assert copiado == ["texto do campo"]
        assert host.status == ["Dados copiados!"]

    def test_documentos_sem_painel_nao_copia(self, monkeypatch):
        copiado: list[str] = []
        fake = type("pyxclip", (), {"copy": staticmethod(copiado.append)})
        monkeypatch.setitem(sys.modules, "pyxclip", fake)

        host = _host(tabs=("Análise do Ticker", "Documentos"))
        host._copy_data()
        assert copiado == []

    def test_documentos_fallback_quando_pyxclip_indisponivel(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pyxclip", None)
        host = _host(tabs=("Análise do Ticker", "Documentos"))
        host._documents_panel = type(
            "P", (), {"texto_atual": lambda self: "texto do campo"}
        )()
        host._copy_data()
        assert host.clipboard == ["texto do campo"]


class TestFallbackClipboardText:
    def test_copia_texto_informado(self):
        host = _host()
        host._fallback_clipboard_text("conteudo")
        assert host.clipboard == ["conteudo"]
        assert host.status == ["Dados copiados! (fallback)"]

    def test_texto_vazio_nao_copia(self):
        host = _host()
        host._fallback_clipboard_text("")
        assert host.clipboard == []
        assert host.status == []
