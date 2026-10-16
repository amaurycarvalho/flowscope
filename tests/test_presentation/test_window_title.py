"""Testes do título dinâmico da janela com o nome do watchlist (headless).

A composição do título e os handlers de estado são exercitados sem ``Tk``:
a lógica pura vive em ``compor_titulo``/``arquivo_watchlist_inicial`` e os
handlers são mixados num host que apenas registra o título aplicado.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flowscope.presentation.gui import app as app_mod
from flowscope.presentation.gui.app import (
    WatchlistTitleMixin,
    arquivo_watchlist_inicial,
    compor_titulo,
)
from flowscope.presentation.gui.app_constants import TITLE_PREFIX


class _HostTitulo(WatchlistTitleMixin):
    """Host headless que registra o título aplicado, sem Tk."""

    def __init__(self, prefs: dict | None = None) -> None:
        self._prefs = {} if prefs is None else prefs
        self._watchlist_file: Path | None = None
        self._watchlist_dirty = False
        self._index_name: str | None = None
        self._controller = MagicMock()
        self._titulo = ""

    def title(self, texto: str | None = None) -> str:
        if texto is not None:
            self._titulo = texto
        return self._titulo


@pytest.fixture
def salvas(monkeypatch):
    """Captura as preferências gravadas, sem tocar no config real."""
    capturado: dict = {}
    monkeypatch.setattr(app_mod, "save_preferences", capturado.update)
    return capturado


class TestComporTitulo:
    def test_sem_arquivo_exibe_nova_lista(self):
        assert compor_titulo(None, None, False) == f"{TITLE_PREFIX} — Nova lista.txt"

    def test_arquivo_exibe_basename_sem_asterisco(self):
        titulo = compor_titulo(Path("/home/user/dados/petr4.txt"), None, False)
        assert titulo == f"{TITLE_PREFIX} — petr4.txt"

    def test_dirty_exibe_asterisco(self):
        titulo = compor_titulo(Path("/home/user/dados/petr4.txt"), None, True)
        assert titulo == f"{TITLE_PREFIX} — petr4.txt*"

    def test_indice_exibe_nome_do_indice(self):
        assert compor_titulo(None, "IBOV.txt", False) == f"{TITLE_PREFIX} — IBOV.txt"


class TestArquivoInicial:
    def test_caminho_guardado_vira_path(self):
        assert arquivo_watchlist_inicial("/home/user/dados/petr4.txt") == Path(
            "/home/user/dados/petr4.txt"
        )

    def test_ausente_ou_invalido_vira_none(self):
        assert arquivo_watchlist_inicial(None) is None
        assert arquivo_watchlist_inicial("") is None
        assert arquivo_watchlist_inicial(42) is None


class TestHandlersTitulo:
    def test_carregar_arquivo_atualiza_titulo_e_limpa_dirty(self, salvas):
        host = _HostTitulo()
        host._watchlist_dirty = True

        host._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        assert host._titulo == f"{TITLE_PREFIX} — petr4.txt"
        assert host._watchlist_dirty is False
        assert host._prefs["last_ticker_file"] == "/home/user/dados/petr4.txt"
        assert salvas["last_ticker_file"] == "/home/user/dados/petr4.txt"

    def test_editar_conteudo_marca_dirty_e_asterisco(self, salvas):
        host = _HostTitulo()
        host._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        host._on_watchlist_content_changed()

        assert host._watchlist_dirty is True
        assert host._titulo == f"{TITLE_PREFIX} — petr4.txt*"

    def test_indice_exibe_nome_do_indice(self, salvas):
        host = _HostTitulo()
        host._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))

        host._on_index_click("IBOV")

        assert host._titulo == f"{TITLE_PREFIX} — IBOV.txt"
        assert host._watchlist_dirty is False
        host._controller.on_index_clicked.assert_called_once_with("IBOV")

    def test_indice_nao_sobrescreve_caminho_guardado(self, salvas):
        host = _HostTitulo()
        host._on_watchlist_file_changed(Path("/home/user/dados/petr4.txt"))
        salvas.clear()

        host._on_index_click("IBOV")

        assert "last_ticker_file" not in salvas
        assert host._prefs["last_ticker_file"] == "/home/user/dados/petr4.txt"

    def test_restauracao_no_startup_usa_basename(self):
        arquivo = arquivo_watchlist_inicial("/home/user/dados/petr4.txt")
        assert compor_titulo(arquivo, None, False) == f"{TITLE_PREFIX} — petr4.txt"
