import platform
import shutil
import sys
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

    ticker_filter = None
    if args.tickers:
        from flowscope.presentation.cli import _load_tickers
        ticker_filter = _load_tickers(args.tickers)

    if args.vwap:
        _export("vwap", ticker_filter)
        return

    run_cli(args)


def _resolve_icon_path(filename: str = "flowscope.png") -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent.parent
    return base / "icons" / filename


def _desktop_path() -> Path:
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "Área de Trabalho"
    return desktop


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


def _open_gui() -> None:
    import logging
    logging.basicConfig(handlers=[logging.NullHandler()], force=True)

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
