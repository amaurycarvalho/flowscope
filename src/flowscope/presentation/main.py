import logging
import platform
import shutil
import sys
import os
import subprocess

from logging.handlers import RotatingFileHandler, SysLogHandler
from pathlib import Path

from flowscope import __version__
from flowscope.presentation.cli import build_parser, run_cli


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"FlowScope v{__version__}")
        return

    if args.create_shortcut:
        if platform.system() != "Linux":
            print("Função disponível apenas no Linux.", file=sys.stderr)
            sys.exit(0)
        success = _create_desktop_shortcut()
        if success:
            print(f"Atalho criado em: {_desktop_path() / 'flowscope.desktop'}")
            sys.exit(0)
        sys.exit(1)

    if args.gui:
        _open_gui()
        return

    has_cli_args = args.tickers is not None or args.vwap
    if has_cli_args:
        ticker_filter = None
        if args.tickers:
            from flowscope.presentation.cli import _load_tickers
            ticker_filter = _load_tickers(args.tickers)

        if args.vwap:
            _export("vwap", ticker_filter)
            return

        run_cli(args)
        return

    _open_gui()


def _resolve_icon_path(filename: str = "flowscope.png") -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "icons" / filename


def _desktop_path() -> Path:
    try:
        result = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True, text=True, timeout=5,
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
    return (_desktop_path() / "flowscope.desktop").exists()


def _create_desktop_shortcut() -> bool:
    if platform.system() != "Linux":
        return False
    desktop = _desktop_path()

    icon_src = _resolve_icon_path()

    icon_dst = Path.home() / ".local" / "share" / "icons" / "flowscope.png"
    icon_dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(icon_src, icon_dst)
    except (OSError, PermissionError):
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
    except (OSError, PermissionError):
        return False


def _configure_logging() -> None:
    log_dir = Path.home() / ".flowscope" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = [
        RotatingFileHandler(log_dir / "flowscope.log", maxBytes=1_000_000, backupCount=3),
    ]

    system = platform.system()
    if system in ("Linux", "Darwin"):
        address = "/dev/log" if system == "Linux" else "/var/run/syslog"
        try:
            handlers.append(SysLogHandler(address=address))
        except OSError:
            pass
    elif system == "Windows":
        try:
            from logging.handlers import NTEventLogHandler
            handlers.append(NTEventLogHandler("FlowScope"))
        except ImportError:
            pass

    logging.basicConfig(level=logging.WARNING, handlers=handlers, force=True)


def _open_gui() -> None:
    _configure_logging()

    from flowscope.presentation.gui.app import FlowScopeGUI

    app = FlowScopeGUI()
    app.mainloop()


def _export(indicator: str, ticker_filter: list[str] | None = None) -> None:
    from datetime import date
    from pathlib import Path

    from flowscope.application.use_cases import ExportVWAPUseCase
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository

    repo = B3DataRepository(B3Client())
    ref_date = date.today()

    use_case = ExportVWAPUseCase(repo)
    content = use_case.execute(ref_date, ticker_filter=ticker_filter)

    output = f"{indicator}_{ref_date}.csv"
    Path(output).write_text(content, encoding="utf-8")
    print(f"Arquivo exportado: {output}")


if __name__ == "__main__":
    main()
