import argparse
import sys
from datetime import date
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
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
    from flowscope.infrastructure.b3.client import B3Client
    from flowscope.infrastructure.b3.repository import B3DataRepository
    from flowscope.application.use_cases import AnalyzeTickersUseCase

    repo = B3DataRepository(B3Client())
    ref_date = date.today()

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
    lines = ["Ticker;VWAP_Periodo"]
    for ticker in tickers:
        data = metrics.get(ticker, {}).get("vwap")
        if data:
            lines.append(f"{ticker};{data['period_vwap']}")
    content = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    return content
