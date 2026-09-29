"""Copia figuras do matplotlib para a área de transferência do sistema operacional."""

import platform
import subprocess
from pathlib import Path

from matplotlib.figure import Figure

from flowscope.application.clipboard_port import (
    ClipboardError as ClipboardPortError,
)


class ClipboardError(Exception):
    """Erro ao tentar copiar uma imagem para a área de transferência."""


#: Caminho temporário padrão do PNG do gráfico.
TMP_PATH = Path("/tmp") / "flowscope_chart.png"


def salvar_png(figure: Figure, path: Path | None = None) -> Path:
    """Renderiza a figura como PNG e retorna o caminho do arquivo.

    Deve rodar na thread da interface: o backend do matplotlib não é seguro
    contra rendering concorrente com o desenho dos charts.
    """
    destino = path if path is not None else TMP_PATH
    figure.savefig(destino, format="png", dpi=150, bbox_inches="tight")
    return destino


def transferir_png(path: Path) -> None:
    """Transfere o arquivo PNG informado para o clipboard conforme o SO.

    Pode rodar fora da thread da interface: só executa o comando nativo.
    """
    system = platform.system()
    if system == "Linux":
        _copy_linux(path)
    elif system == "Windows":
        _copy_windows(path)
    elif system == "Darwin":
        _copy_macos(path)
    else:
        raise ClipboardError(
            f"Clipboard de imagem não suportado em {system}"
        )


def copy_image_to_clipboard(figure: Figure) -> None:
    """Salva a figura como imagem PNG e a copia para a área de transferência conforme o SO."""
    transferir_png(salvar_png(figure))


class ClipboardImageAdapter:
    """Adaptador da porta de clipboard sobre o clipboard do sistema."""

    def salvar_png(self: "ClipboardImageAdapter", figure: Figure) -> Path:
        """Renderiza a figura, traduzindo o erro de infraestrutura."""
        try:
            return salvar_png(figure)
        except ClipboardError as exc:
            raise ClipboardPortError(str(exc)) from exc

    def transferir_png(self: "ClipboardImageAdapter", path: Path) -> None:
        """Transfere o PNG, traduzindo o erro de infraestrutura."""
        try:
            transferir_png(path)
        except ClipboardError as exc:
            raise ClipboardPortError(str(exc)) from exc

    def copy_image(self: "ClipboardImageAdapter", figure: Figure) -> None:
        """Copia a figura, traduzindo o erro de infraestrutura para a aplicação."""
        try:
            copy_image_to_clipboard(figure)
        except ClipboardError as exc:
            raise ClipboardPortError(str(exc)) from exc


def _copy_linux(path: Path) -> None:
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", str(path)],
            check=True,
        )
    except FileNotFoundError:
        raise ClipboardError(
            "xclip não encontrado. Instale com: sudo apt install xclip"
        )
    except subprocess.CalledProcessError as e:
        raise ClipboardError(f"Erro ao copiar imagem: {e}")


def _copy_windows(path: Path) -> None:
    try:
        import io

        import win32clipboard
        from PIL import Image

        image = Image.open(path)
        output = io.BytesIO()
        image.convert("RGB").save(output, format="BMP")
        data = output.getvalue()[14:]
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
    except ImportError:
        _fallback_powershell(path)
    except (OSError, win32clipboard.error) as e:
        raise ClipboardError(f"Erro ao copiar imagem: {e}")


def _fallback_powershell(path: Path) -> None:
    try:
        subprocess.run(
            [
                "powershell", "-command",
                (f"Add-Type -AssemblyName System.Drawing; "
                f"$img = [System.Drawing.Image]::FromFile('{path}'); "
                f"[System.Windows.Forms.Clipboard]::SetImage($img)"),
            ],
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise ClipboardError(f"Erro ao copiar imagem via PowerShell: {e}")


def _copy_macos(path: Path) -> None:
    try:
        import subprocess
        result = subprocess.run(
            [
                "osascript", "-e",
                f'set the clipboard to (read (POSIX file "{path}") as JPEG picture)',
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise ClipboardError(
                f"Erro ao copiar imagem no macOS: {result.stderr}"
            )
    except FileNotFoundError:
        raise ClipboardError(
            "osascript não encontrado no macOS."
        )
