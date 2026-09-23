"""Testes do painel da aba "Sobre"."""

import os
import tkinter as tk
from unittest.mock import MagicMock

import pytest

from flowscope import __release_date__, __version__
from flowscope.presentation.gui.widgets.about_panel import (
    APRESENTACAO,
    LICENCA,
    AboutPanel,
)

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


@pytest.fixture
def root():
    r = tk.Tk()
    yield r
    r.destroy()


def _percorrer(widget):
    for filho in widget.winfo_children():
        yield filho
        yield from _percorrer(filho)


def _textos(panel):
    return [
        w.cget("text")
        for w in _percorrer(panel._content)
        if isinstance(w, tk.Label) and w.cget("text")
    ]


def _botoes(panel):
    return [w for w in _percorrer(panel._content) if isinstance(w, tk.Button)]


@needs_display
class TestConteudo:
    def test_ordem_das_informacoes(self, root):
        panel = AboutPanel(root)
        textos = _textos(panel)
        assert textos[0] == f"FlowScope v{__version__}"
        assert textos[1] == __release_date__
        assert textos[2] == LICENCA
        assert textos[3] == APRESENTACAO

    def test_icone_renderizado_quando_informado(self, root):
        icone = tk.PhotoImage(width=2, height=2)
        panel = AboutPanel(root, icon=icone)
        com_imagem = [
            w
            for w in _percorrer(panel._content)
            if isinstance(w, tk.Label) and str(w.cget("image"))
        ]
        assert com_imagem

    def test_botoes_acionam_callbacks(self, root):
        repo = MagicMock()
        log = MagicMock()
        panel = AboutPanel(root, on_open_repository=repo, on_open_log=log)
        por_texto = {b.cget("text"): b for b in _botoes(panel)}
        por_texto["Repositório no GitHub"].invoke()
        por_texto["Abrir log da aplicação"].invoke()
        repo.assert_called_once()
        log.assert_called_once()

    def test_conteudo_rolavel(self, root):
        panel = AboutPanel(root)
        assert panel._canvas.cget("yscrollcommand")
        assert panel._canvas.bind("<Configure>")

    def test_grupo_de_botoes_centralizado(self, root):
        panel = AboutPanel(root)
        grupos = [
            w
            for w in _percorrer(panel._content)
            if isinstance(w, tk.Frame)
            and any(
                isinstance(c, tk.Button)
                and c.cget("text") == "Repositório no GitHub"
                for c in w.winfo_children()
            )
        ]
        assert grupos and grupos[0].pack_info()["anchor"] == "center"


@needs_display
class TestAvisoDeNovaVersao:
    def test_sem_aviso_por_padrao(self, root):
        panel = AboutPanel(root)
        assert not any("Nova versão" in texto for texto in _textos(panel))

    def test_show_update_exibe_aviso_e_botao(self, root):
        abre = MagicMock()
        panel = AboutPanel(root)
        panel.show_update("9.9.9", abre)
        assert "Nova versão v9.9.9 disponível" in _textos(panel)
        botoes = [
            b
            for b in _botoes(panel)
            if b.cget("text") == "Abrir página da release"
        ]
        assert len(botoes) == 1
        botoes[0].invoke()
        abre.assert_called_once()

    def test_botao_da_release_centralizado(self, root):
        panel = AboutPanel(root)
        panel.show_update("9.9.9", MagicMock())
        botoes = [
            b
            for b in _botoes(panel)
            if b.cget("text") == "Abrir página da release"
        ]
        assert botoes[0].pack_info()["anchor"] == "center"

    def test_show_update_nao_duplica_avisos(self, root):
        panel = AboutPanel(root)
        panel.show_update("9.9.9", MagicMock())
        panel.show_update("10.0.0", MagicMock())
        avisos = [t for t in _textos(panel) if t.startswith("Nova versão")]
        assert avisos == ["Nova versão v10.0.0 disponível"]
