"""Ponto de entrada principal do FlowScope, orquestrando GUI e linha de comando."""

import argparse
import logging
import platform
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, SysLogHandler
from pathlib import Path

from flowscope import __version__
from flowscope.presentation.cli import build_parser, run_cli
from flowscope.presentation.shortcuts import (
    _create_desktop_shortcut,
    _desktop_path,
    _desktop_shortcut_exists,
    _resolve_icon_path,
)

__all__ = [
    "_create_desktop_shortcut",
    "_desktop_shortcut_exists",
    "_resolve_icon_path",
    "main",
]


def main() -> None:
    """Executa o fluxo principal, interpretando os argumentos e delegando para GUI ou CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(f"FlowScope v{__version__}")
        return

    if args.create_shortcut:
        _create_shortcut_or_exit()
        return

    if args.gui:
        _open_gui()
        return

    has_cli_args = args.tickers is not None or args.vwap
    if has_cli_args:
        _handle_cli_args(args)
        return

    _open_gui()


def _create_shortcut_or_exit() -> None:
    """Cria o atalho do desktop ou encerra o processo com código de erro adequado."""
    if platform.system() != "Linux":
        print("Função disponível apenas no Linux.", file=sys.stderr)
        sys.exit(0)
    success = _create_desktop_shortcut()
    if success:
        print(f"Atalho criado em: {_desktop_path() / 'flowscope.desktop'}")
        sys.exit(0)
    sys.exit(1)


def _handle_cli_args(args: argparse.Namespace) -> None:
    """Delega para o modo CLI, exportando o VWAP em CSV quando solicitado."""
    ticker_filter = None
    if args.tickers:
        from flowscope.presentation.cli import _load_tickers
        ticker_filter = _load_tickers(args.tickers)

    if args.vwap:
        _export("vwap", ticker_filter)
        return

    run_cli(args)


class _MillisecondFormatter(logging.Formatter):
    def formatTime(
        self: "_MillisecondFormatter",
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        created = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone()
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S"
        formatted = created.strftime(datefmt)
        if "%f" in datefmt:
            formatted = formatted.replace(
                created.strftime("%f"), f"{created.microsecond // 1000:03d}"
            )
        return formatted


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

    formatter = _MillisecondFormatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S,%f",
    )
    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=handlers, force=True)


def _open_gui() -> None:
    _configure_logging()

    from flowscope.presentation.gui.app import FlowScopeGUI

    app = FlowScopeGUI()
    app.mainloop()


def _export(indicator: str, ticker_filter: list[str] | None = None) -> None:
    from datetime import datetime, timezone
    from pathlib import Path

    from flowscope.application.use_cases import ExportVWAPUseCase
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository

    repo = B3DataRepository(B3Client())
    ref_date = datetime.now(timezone.utc).date()

    use_case = ExportVWAPUseCase(repo)
    content = use_case.execute(ref_date, ticker_filter=ticker_filter)

    output = f"{indicator}_{ref_date}.csv"
    Path(output).write_text(content, encoding="utf-8")
    print(f"Arquivo exportado: {output}")


if __name__ == "__main__":
    main()
