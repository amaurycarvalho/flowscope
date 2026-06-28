import sys

from flowscope import __version__
from flowscope.presentation.cli import build_parser, run_cli


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"FlowScope v{__version__}")
        return

    if args.create_shortcut:
        _create_desktop_shortcut()
        return

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


def _create_desktop_shortcut() -> None:
    import platform

    if platform.system() != "Linux":
        print(
            "Função disponível apenas no Linux.",
            file=sys.stderr,
        )
        sys.exit(0)

    from pathlib import Path

    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "Área de Trabalho"

    icon_path = Path(__file__).resolve().parent.parent / "icons" / "flowscope.png"
    executable = sys.argv[0]

    content = (
        "[Desktop Entry]\n"
        "Name=FlowScope\n"
        f"Exec={executable}\n"
        "Type=Application\n"
        "Terminal=false\n"
        f"Icon={icon_path}\n"
        "Categories=Finance;Office;\n"
    )

    shortcut = desktop / "flowscope.desktop"
    try:
        shortcut.write_text(content, encoding="utf-8")
        shortcut.chmod(0o755)
        print(f"Atalho criado em: {shortcut}")
    except (OSError, PermissionError) as e:
        print(
            f"Erro ao criar atalho: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


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
