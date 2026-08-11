"""Utilitários para criação de atalhos de desktop e localização de recursos."""

import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _resolve_icon_path(filename: str = "flowscope.png") -> Path:
    """Localiza o caminho do ícone do FlowScope em modo de desenvolvimento ou empacotado."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "icons" / filename


def _desktop_path() -> Path:
    """Retorna o caminho do diretório Desktop do usuário atual."""
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5,
            check=False,
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            if path:
                return Path(path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    user_dirs = Path.home() / ".config" / "user-dirs.dirs"
    if user_dirs.is_file():
        for line in user_dirs.read_text().splitlines():
            if line.startswith("XDG_DESKTOP_DIR="):
                raw = line.split("=", 1)[1].strip().strip('"')
                expanded = raw.replace("$HOME", str(Path.home()))
                if expanded:
                    return Path(expanded)
    return Path.home() / "Desktop"


def _desktop_shortcut_exists() -> bool:
    """Verifica se o atalho do FlowScope já existe no desktop."""
    return (_desktop_path() / "flowscope.desktop").exists()


def _create_desktop_shortcut() -> bool:
    """Cria o atalho do FlowScope no desktop e copia o ícone para o usuário."""
    if platform.system() != "Linux":
        return False
    desktop = _desktop_path()

    icon_src = _resolve_icon_path()

    icon_dst = Path.home() / ".local" / "share" / "icons" / "flowscope.png"
    icon_dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(icon_src, icon_dst)
    except OSError:
        return False

    executable = str(Path(sys.argv[0]).resolve())

    content = (
        "[Desktop Entry]\n"
        "Name=FlowScope\n"
        f"Exec={executable} --gui\n"
        "Type=Application\n"
        "Terminal=false\n"
        f"Icon={icon_dst}\n"
        "Categories=Finance;Office;\n"
        "StartupNotify=true\n"
    )

    shortcut = desktop / "flowscope.desktop"
    try:
        shortcut.write_text(content, encoding="utf-8")
        shortcut.chmod(0o755)
        return True
    except OSError:
        return False
