"""Testes do adaptador da porta de clipboard de imagens."""

import pytest

from flowscope.application.clipboard_port import ClipboardError as PortClipboardError
from flowscope.infrastructure import clipboard_image
from flowscope.infrastructure.clipboard_image import (
    ClipboardError,
    ClipboardImageAdapter,
)


class TestClipboardImageAdapter:
    def test_sucesso_delega_a_copia(self, monkeypatch):
        chamadas: list = []
        monkeypatch.setattr(
            clipboard_image,
            "copy_image_to_clipboard",
            lambda figure: chamadas.append(figure),
        )
        figura = object()

        ClipboardImageAdapter().copy_image(figura)

        assert chamadas == [figura]

    def test_falha_e_traduzida_para_a_aplicacao(self, monkeypatch):
        def _falha(_figure):
            raise ClipboardError("xclip ausente")

        monkeypatch.setattr(
            clipboard_image, "copy_image_to_clipboard", _falha
        )

        with pytest.raises(PortClipboardError, match="xclip ausente"):
            ClipboardImageAdapter().copy_image(object())

    def test_salvar_png_delega(self, monkeypatch):
        caminho = clipboard_image.TMP_PATH
        monkeypatch.setattr(
            clipboard_image, "salvar_png", lambda figure: caminho
        )

        assert ClipboardImageAdapter().salvar_png(object()) == caminho

    def test_transferir_png_delega(self, monkeypatch):
        chamadas: list = []
        monkeypatch.setattr(
            clipboard_image,
            "transferir_png",
            lambda path: chamadas.append(path),
        )

        ClipboardImageAdapter().transferir_png(clipboard_image.TMP_PATH)

        assert chamadas == [clipboard_image.TMP_PATH]

    def test_salvar_png_traduz_erro(self, monkeypatch):
        def _falha(_figure):
            raise ClipboardError("sem espaço")

        monkeypatch.setattr(clipboard_image, "salvar_png", _falha)

        with pytest.raises(PortClipboardError, match="sem espaço"):
            ClipboardImageAdapter().salvar_png(object())

    def test_transferir_png_traduz_erro(self, monkeypatch):
        def _falha(_path):
            raise ClipboardError("xclip ausente")

        monkeypatch.setattr(clipboard_image, "transferir_png", _falha)

        with pytest.raises(PortClipboardError, match="xclip ausente"):
            ClipboardImageAdapter().transferir_png(clipboard_image.TMP_PATH)
