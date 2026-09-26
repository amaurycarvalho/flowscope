"""Testes da cópia de gráfico via porta de clipboard."""

from unittest.mock import MagicMock

from flowscope.application.clipboard_port import ClipboardError
from flowscope.presentation.gui.app_actions import ActionsMixin


class TestCopyChart:
    def test_copia_com_sucesso(self):
        host = MagicMock()
        figura = object()

        ActionsMixin._copy_chart(host, figura)

        host._clipboard.copy_image.assert_called_once_with(figura)
        host._flash_status.assert_called_once_with("Gráfico copiado!")

    def test_erro_de_clipboard_vira_status(self):
        host = MagicMock()
        host._clipboard.copy_image.side_effect = ClipboardError("xclip ausente")

        ActionsMixin._copy_chart(host, object())

        host._set_status.assert_called_once_with("Erro: xclip ausente", "⚠")

    def test_sem_porta_nao_falha(self):
        host = MagicMock()
        host._clipboard = None

        ActionsMixin._copy_chart(host, object())

        host._flash_status.assert_not_called()
