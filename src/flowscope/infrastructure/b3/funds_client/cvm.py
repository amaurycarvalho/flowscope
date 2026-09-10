"""Construção do índice ticker→codeCVM a partir do cadastro da B3."""

import csv
import io

from flowscope.infrastructure.b3.funds_client.texto import _normalizar_rotulo


def _normalizar_code_cvm(valor: str) -> str:
    """Remove os zeros à esquerda de um código CVM."""
    valor = valor.strip()
    normalizado = valor.lstrip("0")
    return normalizado or "0"


def montar_indice_code_cvm(texto_csv: str) -> dict[str, str]:
    """Constrói o índice ticker→codeCVM a partir do CSV do cadastro da B3."""
    if not texto_csv:
        return {}
    dialeto = csv.Sniffer().sniff(texto_csv[:4096], delimiters=";,|")
    leitor = csv.DictReader(io.StringIO(texto_csv), delimiter=dialeto.delimiter)
    coluna_cvm = _coluna_com(leitor.fieldnames, ["cvm"])
    coluna_ticker = _coluna_com(
        leitor.fieldnames,
        ["ticker", "codnegociacao", "codigodenegociacao", "acao", "codigo"],
    )
    if coluna_cvm is None or coluna_ticker is None:
        return {}
    indice: dict[str, str] = {}
    for linha in leitor:
        ticker = str(linha.get(coluna_ticker) or "").strip().upper()
        codigo = str(linha.get(coluna_cvm) or "").strip()
        if not ticker or not codigo.isdigit():
            continue
        indice[ticker] = _normalizar_code_cvm(codigo)
    return indice


def _coluna_com(colunas: list[str] | None, termos: list[str]) -> str | None:
    """Retorna a primeira coluna cujo nome contém um dos termos informados."""
    if not colunas:
        return None
    normalizadas = {_normalizar_rotulo(coluna): coluna for coluna in colunas}
    for coluna_normalizada, coluna in normalizadas.items():
        if any(termo in coluna_normalizada for termo in termos):
            return coluna
    return None
