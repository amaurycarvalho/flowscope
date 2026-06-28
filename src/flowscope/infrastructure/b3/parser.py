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
    pass


def parse_csv(content: str, segment_filter: str | None = "CASH") -> list[TradeDay]:
    lines = content.splitlines()
    data_start = 1 if lines and not lines[0].startswith("RptDt") else 0
    reader = csv.DictReader(lines[data_start:], delimiter=";")
    if reader.fieldnames is None:
        raise ParseError("CSV sem cabeçalho")

    header = [h.strip() for h in reader.fieldnames]
    if not all(col in header for col in _EXPECTED_HEADER):
        raise ParseError(
            "Cabeçalho do CSV não contém as colunas esperadas. "
            f"Esperado: {_EXPECTED_HEADER}, Encontrado: {header}"
        )

    trades: list[TradeDay] = []
    for row_num, row in enumerate(reader, start=2):
        try:
            segment = row.get("SgmtNm", "").strip()
            if segment_filter is not None and segment != segment_filter:
                continue

            ticker_str = row.get("TckrSymb", "").strip()
            if not ticker_str:
                continue
            fin_vol_str = row.get("NtlFinVol", "").strip()
            if not fin_vol_str:
                continue
            avg_price_str = row.get("TradAvrgPric", "").strip()
            if not avg_price_str:
                continue

            trade = TradeDay(
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
            trades.append(trade)
        except (ValueError, InvalidOperation, ParseError):
            continue
    return trades


def parse_index_csv(content: str) -> list[str]:
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
        if ticker.startswith("Quantidade") or ticker.startswith("Redutor"):
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
        return Decimal("0")
    return Decimal(value)
