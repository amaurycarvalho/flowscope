"""Porta de cópia de imagens para a área de transferência do sistema.

A apresentação copia figuras por meio desta porta, implementada em
``infrastructure`` conforme o sistema operacional. O erro de clipboard é
declarado na aplicação para que a apresentação não dependa de ``infrastructure``.

A cópia é decomposta em duas etapas para permitir orquestração assíncrona: o
rendering da figura (:meth:`ImageClipboardPort.salvar_png`) permanece na thread
da interface, e a transferência do PNG (:meth:`ImageClipboardPort.transferir_png`)
pode rodar fora dela. :meth:`ImageClipboardPort.copy_image` permanece intacta
para os chamadores síncronos.
"""

from pathlib import Path
from typing import Protocol, runtime_checkable


class ClipboardError(Exception):
    """Erro ao copiar uma imagem para a área de transferência."""


@runtime_checkable
class ImageClipboardPort(Protocol):
    """Contrato de cópia de uma figura para a área de transferência."""

    def salvar_png(self: "ImageClipboardPort", figure: object) -> Path:
        """Renderiza a figura como PNG e retorna o caminho do arquivo."""
        ...

    def transferir_png(self: "ImageClipboardPort", path: Path) -> None:
        """Transfere o arquivo PNG informado para o clipboard do sistema."""
        ...

    def copy_image(self: "ImageClipboardPort", figure: object) -> None:
        """Copia a figura para a área de transferência do sistema operacional."""
        ...
