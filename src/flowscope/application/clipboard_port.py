"""Porta de cópia de imagens para a área de transferência do sistema.

A apresentação copia figuras por meio desta porta, implementada em
``infrastructure`` conforme o sistema operacional. O erro de clipboard é
declarado na aplicação para que a apresentação não dependa de ``infrastructure``.
"""

from typing import Protocol, runtime_checkable


class ClipboardError(Exception):
    """Erro ao copiar uma imagem para a área de transferência."""


@runtime_checkable
class ImageClipboardPort(Protocol):
    """Contrato de cópia de uma figura para a área de transferência."""

    def copy_image(self: "ImageClipboardPort", figure: object) -> None:
        """Copia a figura para a área de transferência do sistema operacional."""
        ...
