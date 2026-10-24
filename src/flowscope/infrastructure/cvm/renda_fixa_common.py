"""Utilitários de leitura dos datasets CVM de renda fixa."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import date
from decimal import Decimal
from functools import lru_cache

from flowscope.domain.renda_fixa import TituloRendaFixa
from flowscope.infrastructure.cvm.datasets import parse_data, parse_decimal

_NAO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")

#: Código CETIP/ISIN: sequência alfanumérica com ao menos um dígito.
_CODIGO = re.compile(r"(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6,}")


class LinhaNormalizada(dict[str, str]):
    """Linha de CSV com os nomes das colunas já normalizados."""


@lru_cache(maxsize=2048)
def _normalizar_texto(texto: str) -> str:
    """Normaliza um texto de coluna, cacheando os nomes repetidos."""
    decomposto = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(
        caractere
        for caractere in decomposto
        if not unicodedata.combining(caractere)
    )
    return _NAO_ALFANUMERICO.sub("_", sem_acento.lower()).strip("_")


def normalizar_coluna(nome: object) -> str:
    """Normaliza o nome de uma coluna para comparação tolerante."""
    return _normalizar_texto(str(nome or ""))


def iter_linhas(conteudo: bytes) -> Iterator[LinhaNormalizada]:
    """Itera um CSV da CVM (latin1, delimitador ``;``) com colunas normalizadas."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return
    colunas = {chave: normalizar_coluna(chave) for chave in leitor.fieldnames}
    for linha in leitor:
        if not any(linha.values()):
            continue
        yield LinhaNormalizada(
            {
                colunas.get(chave, normalizar_coluna(chave)): valor
                for chave, valor in linha.items()
            }
        )


def ler_linhas(conteudo: bytes) -> list[LinhaNormalizada]:
    """Lê um CSV da CVM como lista de linhas normalizadas."""
    return list(iter_linhas(conteudo))


def valor(linha: Mapping[str, str], *nomes: str) -> str | None:
    """Retorna o primeiro valor não vazio entre as colunas candidatas."""
    for nome in nomes:
        texto = str(linha.get(normalizar_coluna(nome)) or "").strip()
        if texto:
            return texto
    if isinstance(linha, LinhaNormalizada):
        return None
    normalizadas = {normalizar_coluna(chave): chave for chave in linha}
    for nome in nomes:
        chave = normalizadas.get(normalizar_coluna(nome))
        if chave is None:
            continue
        texto = str(linha.get(chave) or "").strip()
        if texto:
            return texto
    return None


def inteiro(linha: Mapping[str, str], *nomes: str) -> int:
    """Retorna o primeiro inteiro válido entre as colunas candidatas."""
    texto = valor(linha, *nomes)
    try:
        return int(str(texto))
    except (TypeError, ValueError):
        return 0


def data(linha: Mapping[str, str], *nomes: str) -> date | None:
    """Retorna a primeira data válida entre as colunas candidatas."""
    for nome in nomes:
        texto = valor(linha, nome)
        if texto:
            convertida = parse_data(texto)
            if convertida is not None:
                return convertida
    return None


def decimal(linha: Mapping[str, str], *nomes: str) -> Decimal | None:
    """Retorna o primeiro decimal válido entre as colunas candidatas."""
    for nome in nomes:
        texto = valor(linha, nome)
        if texto:
            convertido = parse_decimal(texto)
            if convertido is not None:
                return convertido
    return None


def codigo_cetip(texto: str | None) -> str | None:
    """Extrai um código CETIP/ISIN de um campo textual da fonte."""
    if not texto:
        return None
    token = _CODIGO.search(texto)
    return token.group(0).upper() if token else None


def nome_arquivo(csvs: Mapping[str, bytes], *prefixos: str) -> bytes | None:
    """Concatena os CSVs cujo nome contém algum dos prefixos informados."""
    partes = [
        conteudo
        for nome, conteudo in csvs.items()
        if any(prefixo in nome for prefixo in prefixos)
    ]
    return b"\n".join(partes) if partes else None


def melhor_por_chave(
    itens: Iterable[TituloRendaFixa],
    chave: Callable[[TituloRendaFixa], str] | None = None,
) -> list[TituloRendaFixa]:
    """Mantém, por chave, o título de maior data de referência."""
    identificar = chave or (lambda item: item.chave_fonte)
    melhores: dict[str, TituloRendaFixa] = {}
    for item in itens:
        identidade = identificar(item)
        atual = melhores.get(identidade)
        if atual is None or _ref_titulo(item) > _ref_titulo(atual):
            melhores[identidade] = item
    return list(melhores.values())


def _ref_titulo(item: TituloRendaFixa) -> date:
    """Chave de comparação da data de referência de um título."""
    return item.data_referencia or date.min
