"""Parsers dos arquivos CSV de negociação e de carteiras da B3."""

import csv
import json
import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from flowscope.domain.entities import TradeDay
from flowscope.domain.index_history import IndexClose
from flowscope.domain.value_objects import Price, Ticker, Volume

logger = logging.getLogger("flowscope")

#: Versão do formato de cache da série histórica dos índices.
INDEX_HISTORY_SCHEMA_VERSION = 1

#: Meses cobertos pela grade ``rateValue1..rateValue12``.
_MESES_GRADE = range(1, 13)

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


def parse_index_history(payload: object, year: int) -> list[IndexClose]:
    """Interpreta a grade dia × mês da evolução diária de um índice.

    ``payload`` é o JSON decodificado do endpoint ``GetPortfolioDay``: cada
    linha de ``results`` traz o dia e as colunas ``rateValue1..12`` com o
    fechamento de cada mês. Valores nulos ou inválidos são ignorados; uma
    resposta vazia ou malformada vira ausência de série (lista vazia).
    """
    dados = _payload_como_dict(payload)
    if dados is None:
        logger.warning("Grade da série do índice com payload inválido")
        return []
    resultados = dados.get("results")
    if not isinstance(resultados, list):
        logger.warning("Grade da série do índice sem a lista 'results'")
        return []
    fechamentos: dict[date, IndexClose] = {}
    for linha in resultados:
        _coletar_linha(fechamentos, linha, year)
    return [fechamentos[data] for data in sorted(fechamentos)]


def _payload_como_dict(payload: object) -> dict | None:
    """Normaliza o payload JSON (texto ou dicionário) em um dicionário."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (TypeError, ValueError):
            return None
    return payload if isinstance(payload, dict) else None


def _coletar_linha(
    fechamentos: dict[date, IndexClose], linha: object, year: int
) -> None:
    """Coleta os fechamentos de uma linha da grade dia × mês."""
    if not isinstance(linha, dict):
        return
    dia = _parse_day(linha.get("day"))
    if dia is None:
        logger.warning(
            "Grade da série do índice: dia inválido %r",
            linha.get("day"),
        )
        return
    for mes in _MESES_GRADE:
        _coletar_celula(fechamentos, linha, dia, mes, year)


def _coletar_celula(
    fechamentos: dict[date, IndexClose],
    linha: dict,
    dia: int,
    mes: int,
    year: int,
) -> None:
    """Coleta o fechamento de uma célula, ignorando valor/data inválidos."""
    valor = _parse_index_decimal(linha.get(f"rateValue{mes}"))
    if valor is None:
        return
    try:
        momento = date(year, mes, dia)
    except ValueError:
        logger.warning(
            "Grade da série do índice: data inválida (%s-%s-%s)",
            year,
            mes,
            dia,
        )
        return
    fechamentos[momento] = IndexClose(date=momento, close=valor)


def _parse_day(value: object) -> int | None:
    """Interpreta o dia da linha da grade, rejeitando valores fora de 1..31."""
    try:
        dia = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return dia if 1 <= dia <= 31 else None


def _parse_index_decimal(value: object) -> Decimal | None:
    """Devolve um fechamento da grade como ``Decimal``, ignorando nulos/inválidos."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        texto = value.strip()
        if not texto:
            return None
        try:
            if "," in texto:
                return Decimal(texto.replace(".", "").replace(",", "."))
            return Decimal(texto)
        except InvalidOperation:
            logger.warning(
                "Grade da série do índice: valor inválido %r", value
            )
            return None
    logger.warning("Grade da série do índice: valor inválido %r", value)
    return None


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
