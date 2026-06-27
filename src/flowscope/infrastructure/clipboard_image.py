import sys
import platform
import subprocess
from pathlib import Path
from matplotlib.figure import Figure


def copy_image_to_clipboard(figure: Figure) -> None:
    system = platform.system()
    tmp_path = Path("/tmp") / "flowscope_chart.png"

    figure.savefig(tmp_path, format="png", dpi=150, bbox_inches="tight")

    if system == "Linux":
        _copy_linux(tmp_path)
    elif system == "Windows":
        _copy_windows(tmp_path)
    elif system == "Darwin":
        _copy_macos(tmp_path)
    else:
        print(
            f"Clipboard de imagem não suportado em {system}",
            file=sys.stderr,
        )


def _copy_linux(path: Path) -> None:
    try:
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", str(path)],
            check=True,
        )
    except FileNotFoundError:
        print(
            "Erro: xclip não encontrado. Instale com: sudo apt install xclip",
            file=sys.stderr,
        )
    except subprocess.CalledProcessError as e:
        print(f"Erro ao copiar imagem: {e}", file=sys.stderr)


def _copy_windows(path: Path) -> None:
    try:
        import win32clipboard
        from PIL import Image
        import io

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
    except Exception as e:
        print(f"Erro ao copiar imagem: {e}", file=sys.stderr)


def _fallback_powershell(path: Path) -> None:
    try:
        subprocess.run(
            [
                "powershell", "-command",
                f"Add-Type -AssemblyName System.Drawing; "
                f"$img = [System.Drawing.Image]::FromFile('{path}'); "
                f"[System.Windows.Forms.Clipboard]::SetImage($img)",
            ],
            check=True,
        )
    except Exception as e:
        print(f"Erro ao copiar imagem via PowerShell: {e}", file=sys.stderr)


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
        )
        if result.returncode != 0:
            print(
                f"Erro ao copiar imagem no macOS: {result.stderr}",
                file=sys.stderr,
            )
    except FileNotFoundError:
        print(
            "Erro: osascript não encontrado no macOS.",
            file=sys.stderr,
        )
