"""Ponto de entrada principal do FlowScope, orquestrando GUI e linha de comando."""

import argparse
import copy
import logging
import multiprocessing
import platform
import sys
import time
from datetime import date, datetime, timezone
from logging.handlers import SysLogHandler, TimedRotatingFileHandler

import requests

from flowscope import __version__
from flowscope.infrastructure.logging.housekeeping import (
    limpar_backups_antigos,
    renomear_backup,
    rotacionar_log_obsoleto,
)
from flowscope.infrastructure.logging.retention import log_retention_days
from flowscope.log_paths import LOG_DATEFMT, LOG_FORMAT, log_dir, log_file_path
from flowscope.presentation.cli import build_parser
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
    multiprocessing.freeze_support()
    parser = build_parser()
    args = parser.parse_args()
    _configure_logging()

    inicio = time.monotonic()
    codigo = 0
    try:
        _executar(args)
    except SystemExit as exc:
        codigo = exc.code if isinstance(exc.code, int) else 1
        raise
    finally:
        _registrar_auditoria(args, inicio, time.monotonic(), codigo)


def _executar(args: argparse.Namespace) -> None:
    """Despacha a invocação para os modos especiais ou a GUI."""
    if _tratar_modos_especiais(args):
        return

    _open_gui()


def _tratar_modos_especiais(args: argparse.Namespace) -> bool:
    """Trata versão, MCP, navegação, leitura e atalho; devolve ``True`` se consumiu."""
    if args.version:
        print(f"FlowScopeBR v{__version__}")
        return True

    if getattr(args, "comando", None) == "mcp":
        from flowscope.presentation.cli import iniciar_mcp

        iniciar_mcp(args.watchlist, args.data)
        return True

    if getattr(args, "comando", None) == "nav":
        from flowscope.presentation.cli import executar_nav

        executar_nav(args)
        return True

    if getattr(args, "comando", None) in ("carregar", "atualizar", "resumir"):
        from flowscope.presentation.cli_acoes import executar_acao

        executar_acao(args)
        return True

    if getattr(args, "comando", None) == "exportar":
        from flowscope.presentation.cli_consultas import executar_exportar

        executar_exportar(args)
        return True

    if getattr(args, "comando", None) == "consultar":
        from flowscope.presentation.cli_consultas import executar_consultar

        executar_consultar(args)
        return True

    if args.create_shortcut:
        _create_shortcut_or_exit()
        return True
    return False


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


#: Argumentos registrados na auditoria da CLI (whitelist; exclui segredos).
_CHAVES_AUDITORIA = (
    "comando",
    "recurso",
    "operacao",
    "caminho",
    "ticker",
    "arquivo",
    "data",
    "data_inicio",
    "data_fim",
    "tickers",
    "palavra",
    "categoria",
    "saida",
    "watchlist",
    "esperar",
)


def _comando_principal(args: argparse.Namespace) -> str:
    """Deriva o rótulo do comando principal de uma invocação."""
    if args.version:
        return "version"
    if args.create_shortcut:
        return "create-shortcut"
    return "gui"


def _argumentos_auditaveis(args: argparse.Namespace) -> dict:
    """Extrai apenas os argumentos permitidos do namespace (sem segredos)."""
    dados: dict = {}
    for chave in _CHAVES_AUDITORIA:
        valor = getattr(args, chave, None)
        if valor is None or valor is False:
            continue
        if isinstance(valor, (str, int, float, bool)):
            dados[chave] = valor
        else:
            dados[chave] = str(valor)
    return dados


def _registrar_auditoria(
    args: argparse.Namespace, inicio: float, fim: float, codigo: int
) -> None:
    """Registra no log da aplicação um registro por invocação da CLI."""
    logging.getLogger("flowscope").info(
        "CLI | comando=%s | args=%s | inicio=%s | fim=%s | duracao=%.3fs | codigo=%s",
        args.comando or _comando_principal(args),
        _argumentos_auditaveis(args),
        datetime.fromtimestamp(inicio, tz=timezone.utc).isoformat(),
        datetime.fromtimestamp(fim, tz=timezone.utc).isoformat(),
        max(fim - inicio, 0.0),
        codigo,
    )


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


def _causa_de_comunicacao(exc_info: tuple | None) -> BaseException | None:
    """Retorna a exceção de comunicação presente na cadeia, se houver.

    Percorre a causa e o contexto para cobrir erros de domínio que encapsulam
    uma falha de rede (ex.: ``NetworkError`` causado por ``RequestException``).
    """
    if not exc_info:
        return None
    erro = exc_info[1]
    while erro is not None:
        if isinstance(erro, requests.RequestException):
            return erro
        erro = erro.__cause__ or erro.__context__
    return None


class _CommunicationAwareFormatter(_MillisecondFormatter):
    """Omite o traceback de falhas de comunicação, mantendo um resumo rastreável.

    Falhas de rede/timeout são previstas nos limites de aquisição e já tratadas
    com fallback; o call stack completo polui o log e sugere exceção não
    capturada. A linha passa a terminar com ``[Tipo: mensagem]``. Exceções que
    não são de comunicação preservam o traceback.
    """

    def format(
        self: "_CommunicationAwareFormatter",
        record: logging.LogRecord,
    ) -> str:
        """Formata o registro, resumindo falhas de comunicação previstas."""
        causa = _causa_de_comunicacao(record.exc_info)
        if causa is None:
            return super().format(record)
        registro = copy.copy(record)
        registro.exc_info = None
        registro.exc_text = None
        return f"{super().format(registro)} [{type(causa).__name__}: {causa}]"


def _silenciar_pypdf() -> None:
    """Silencia o logger do ``pypdf`` abaixo de ``ERROR``.

    Os avisos de autorreparo de PDFs malformados ("Ignoring wrong pointing
    object …") são ruído: só ``ERROR`` ou acima é preservado (na configuração do
    app, gravado nos handlers de arquivo/syslog).
    """
    logging.getLogger("pypdf").setLevel(logging.ERROR)


def _configure_logging() -> None:
    diretorio = log_dir()
    diretorio.mkdir(parents=True, exist_ok=True)

    log_path = log_file_path()
    hoje = date.today()
    rotacionar_log_obsoleto(log_path, hoje)
    limpar_backups_antigos(diretorio, hoje, log_retention_days())

    handler = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding="utf-8",
    )
    handler.namer = renomear_backup
    handlers: list[logging.Handler] = [handler]

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

    formatter = _CommunicationAwareFormatter(
        LOG_FORMAT,
        datefmt=LOG_DATEFMT,
    )
    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=handlers, force=True)
    logging.getLogger("flowscope").setLevel(logging.INFO)
    _silenciar_pypdf()


def _open_gui() -> None:
    from flowscope.presentation.gui.app import FlowScopeGUI

    app = FlowScopeGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
