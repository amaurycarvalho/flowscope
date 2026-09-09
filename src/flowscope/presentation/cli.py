"""Interface de linha de comando do FlowScope."""

import argparse
import json
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from flowscope.domain.structured import DocumentoProvento


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="flowscope",
        description="Plataforma de análise quantitativa de fluxo de ordens",
        epilog="Documentação: https://github.com/amaurycarvalho/flowscope",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abrir interface gráfica",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo texto com lista de tickers (um por linha)",
    )
    parser.add_argument(
        "--vwap",
        action="store_true",
        help="Exportar VWAP em CSV",
    )
    parser.add_argument(
        "--structured-earnings",
        type=str,
        metavar="TICKER",
        help="Extrair rendimentos e amortizações estruturados do ticker",
    )
    parser.add_argument(
        "--data-inicio",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        help="Data de início da consulta de proventos",
    )
    parser.add_argument(
        "--data-fim",
        type=_parse_data,
        metavar="AAAA-MM-DD",
        help="Data de fim da consulta de proventos",
    )
    parser.add_argument(
        "--output",
        type=str,
        metavar="ARQUIVO",
        help="Arquivo JSON de saída da extração estruturada",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Exibir versão",
    )
    parser.add_argument(
        "--create-shortcut",
        action="store_true",
        help="Criar atalho no desktop (Linux)",
    )
    return parser


def _parse_data(valor: str) -> date:
    """Interpreta o argumento de data no formato ``AAAA-MM-DD``."""
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Data inválida: {valor!r} (use o formato AAAA-MM-DD)"
        ) from None


def _load_tickers(path: str) -> list[str]:
    filepath = Path(path)
    if not filepath.exists():
        print(f"Erro: arquivo de tickers não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    tickers = [
        line.strip().upper()
        for line in filepath.read_text().splitlines()
        if line.strip()
    ]
    if not tickers:
        print(f"Erro: arquivo de tickers está vazio: {path}", file=sys.stderr)
        sys.exit(1)
    return tickers


def run_cli(args: argparse.Namespace) -> None:
    """Executa a análise dos tickers informados e exibe os resultados."""
    from flowscope.application.use_cases import AnalyzeTickersUseCase
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository

    repo = B3DataRepository(B3Client())
    ref_date = datetime.now(timezone.utc).date()

    tickers = None
    if args.tickers:
        tickers = _load_tickers(args.tickers)

    use_case = AnalyzeTickersUseCase(repo)
    result = use_case.execute(ref_date, tickers)

    if not result:
        print("Nenhum dado disponível para o período.")
        return

    print("=== FlowScope - Análise de Indicadores ===")
    print(f"Data de referência: {ref_date}")
    print()
    for ticker, data in result.items():
        vwap_info = data.get("vwap")
        cvd_info = data.get("cvd")
        if vwap_info:
            print(f"{ticker}: VWAP={vwap_info['period_vwap']:.4f}")
        if cvd_info:
            print(f"{ticker}: CVD={cvd_info['accumulated_cvd']:.2f}")


def export_vwap_csv(
    tickers: list[str],
    metrics: dict,
    output_path: str | None = None,
) -> str:
    """Gera o conteúdo CSV com o VWAP por ticker e opcionalmente grava em arquivo."""
    lines = ["Ticker;VWAP_Periodo"]
    for ticker in tickers:
        data = metrics.get(ticker, {}).get("vwap")
        if data:
            lines.append(f"{ticker};{data['period_vwap']}")
    content = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    return content


def run_structured_earnings(args: argparse.Namespace) -> list[DocumentoProvento]:
    """Executa a extração estruturada de proventos do ticker informado."""
    from flowscope.application.structured_use_cases import ExtrairProventosUseCase
    from flowscope.infrastructure.b3.funds_client import B3FundosClient
    from flowscope.infrastructure.b3.structured_repository import FundosRepository

    ticker = args.structured_earnings.upper()
    repo = FundosRepository(B3FundosClient())
    use_case = ExtrairProventosUseCase(repo)
    documentos = use_case.execute(
        ticker,
        data_inicio=args.data_inicio,
        data_fim=args.data_fim,
        progress_callback=_progresso,
    )

    if args.output:
        Path(args.output).write_text(
            json.dumps(
                [d.to_dict() for d in documentos],
                indent=2,
                ensure_ascii=False,
                default=_json_default,
            ),
            encoding="utf-8",
        )
        if documentos:
            print(f"Extração concluída: {len(documentos)} provento(s) em {args.output}")
    else:
        if not documentos:
            print(f"Nenhum dado disponível para {ticker}")
        else:
            print(
                json.dumps(
                    [d.to_dict() for d in documentos],
                    indent=2,
                    ensure_ascii=False,
                    default=_json_default,
                )
            )
    return documentos


def _progresso(mensagem: str, erro: bool) -> None:
    """Exibe o progresso da extração em stderr, sem poluir a saída JSON."""
    prefixo = "ERRO: " if erro else ""
    print(f"{prefixo}{mensagem}", file=sys.stderr)


def _json_default(valor: object) -> str:
    """Serializa valores não nativos do JSON, como ``Decimal`` e ``date``."""
    if isinstance(valor, (Decimal, date)):
        return str(valor)
    raise TypeError(f"Objeto não serializável: {type(valor).__name__}")
