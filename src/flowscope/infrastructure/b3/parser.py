"""Parsers dos arquivos CSV de negociação e de carteiras da B3."""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation

from flowscope.domain.entities import TradeDay
from flowscope.domain.value_objects import Price, Ticker, Volume

_EXPECTED_HEADER = [
    "RptDt", "TckrSymb", "SgmtNm", "MinPric", "MaxPric",
    "TradAvrgPric", "LastPric", "TradQty", "NtlFinVol", "FinInstrmQty",
]


class ParseError(Exception):
    """Erro ao interpretar o conteúdo de um arquivo da B3."""


def parse_csv(content: str, segment_filter: str | None = "CASH") -> list[TradeDay]:
    """Lê o conteúdo CSV de negociações e retorna a lista de objetos TradeDay."""
    lines = content.splitlines()
    data_start = 1 if lines and not lines[0].startswith("RptDt") else 0
    reader = csv.DictReader(lines[data_start:], delimiter=";")
    _validate_header(reader)

    trades: list[TradeDay] = []
    for row_num, row in enumerate(reader, start=2):
        try:
            trade = _row_to_trade(row, segment_filter, row_num)
            if trade is not None:
                trades.append(trade)
        except (ValueError, InvalidOperation, ParseError):
            continue
    return trades


def _validate_header(reader: csv.DictReader) -> None:
    """Valida o cabeçalho do CSV e levanta ParseError quando ele está fora do esperado."""
    if reader.fieldnames is None:
        raise ParseError("CSV sem cabeçalho")

    header = [h.strip() for h in reader.fieldnames]
    if not all(col in header for col in _EXPECTED_HEADER):
        raise ParseError(
            "Cabeçalho do CSV não contém as colunas esperadas. "
            f"Esperado: {_EXPECTED_HEADER}, Encontrado: {header}"
        )


def _row_to_trade(
    row: dict[str, str], segment_filter: str | None, row_num: int
) -> TradeDay | None:
    """Transforma uma linha do CSV em um TradeDay, respeitando o filtro de segmento."""
    segment = row.get("SgmtNm", "").strip()
    if segment_filter is not None and segment != segment_filter:
        return None

    ticker_str = row.get("TckrSymb", "").strip()
    if not ticker_str:
        return None
    fin_vol_str = row.get("NtlFinVol", "").strip()
    if not fin_vol_str:
        return None
    avg_price_str = row.get("TradAvrgPric", "").strip()
    if not avg_price_str:
        return None

    return TradeDay(
        date=_parse_date(row.get("RptDt", ""), row_num),
        ticker=Ticker(ticker_str),
        segment=segment,
        min_price=Price(_parse_decimal(row.get("MinPric", "0"), row_num)),
        max_price=Price(_parse_decimal(row.get("MaxPric", "0"), row_num)),
        avg_price=Price(_parse_decimal(avg_price_str, row_num)),
        last_price=Price(_parse_decimal(row.get("LastPric", "0"), row_num)),
        trades_qty=Volume(int(_parse_decimal(row.get("TradQty", "0"), row_num))),
        fin_vol=_parse_decimal(fin_vol_str, row_num),
        fin_instr_qty=int(_parse_decimal(row.get("FinInstrmQty", "0"), row_num)),
    )


def parse_index_csv(content: str) -> list[str]:
    """Extrai a lista de tickers válidos do conteúdo CSV de uma carteira de índice."""
    tickers: list[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(";")
        ticker = parts[0].strip()
        if not ticker:
            continue
        if ticker in ("Código", "C\u00f3digo"):
            continue
        if ticker.startswith(("Quantidade", "Redutor")):
            continue
        if not (ticker.isascii() and ticker.isupper()):
            continue
        tickers.append(ticker)
    return tickers


def _parse_date(value: str, row_num: int) -> date:
    value = value.strip()
    if not value:
        raise ParseError(f"Data vazia na linha {row_num}")
    parts = value.split("-")
    if len(parts) == 3:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    parts = value.split("/")
    if len(parts) == 3:
        if len(parts[2]) == 4:
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    raise ParseError(f"Formato de data inválido na linha {row_num}: {value}")


def _parse_decimal(value: str, row_num: int) -> Decimal:
    value = value.strip().replace(",", ".")
    if not value:
        return Decimal(0)
    return Decimal(value)
