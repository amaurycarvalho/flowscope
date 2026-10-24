"""Filtro dos CSVs do SECURIT para os títulos ligados a um ticker."""

from __future__ import annotations

import csv
import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from functools import lru_cache

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.domain.renda_fixa import TipoTitulo, chave_securit, cnpj_valido
from flowscope.infrastructure.cvm.renda_fixa_common import (
    LinhaNormalizada,
    codigo_cetip,
    normalizar_coluna,
    valor,
)

#: Campos que identificam o título em qualquer classe de CSV.
_CAMPOS_IDENTIDADE = (
    "Codigo_CETIP",
    "CETIP",
    "Codigo_ISIN",
    "ISIN",
    "Codigo_Identificacao_Certificado",
    "Codigo_Identificacao",
)

#: Campos de CNPJ usados para casar o devedor econômico.
_CAMPOS_CNPJ = (
    "CNPJ_Cedente_Devedor",
    "CNPJ_Devedor",
    "CNPJ",
    "CNPJ_Parte",
)


def classe_csv(nome: str) -> str | None:
    """Classifica o CSV do SECURIT pela parte do nome."""
    texto = normalizar_coluna(nome)
    for classe in (
        "cedente_devedor",
        "direitos_creditorios",
        "ativo_passivo",
        "carteira",
        "creditos",
        "classe",
        "geral",
    ):
        if classe in texto:
            return classe
    return None


def chave_linha(linha: Mapping[str, str], tipo: TipoTitulo) -> str:
    """Deriva a chave de agrupamento da linha do SECURIT."""
    codigo_cetip_ = codigo_cetip(valor(linha, "Codigo_CETIP", "CETIP"))
    codigo_isin_ = codigo_cetip(valor(linha, "Codigo_ISIN", "ISIN"))
    cnpj_emissor = cnpj_normalizado(
        valor(linha, "CNPJ_Emissora", "CNPJ_Emissor")
    )
    identificacao = valor(
        linha, "Codigo_Identificacao_Certificado", "Codigo_Identificacao"
    )
    if not codigo_cetip_ and not codigo_isin_ and not cnpj_emissor:
        return ""
    return chave_securit(
        codigo_cetip_, codigo_isin_, cnpj_emissor, identificacao
    )


@lru_cache(maxsize=4096)
def cnpj_normalizado(valor_cnpj: str | None) -> str | None:
    """Normaliza e valida o CNPJ, devolvendo ``None`` quando inválido."""
    normalizado = normalizar_cnpj(valor_cnpj)
    return normalizado if cnpj_valido(normalizado) else None


def chaves_alvo(
    csvs: Mapping[str, bytes],
    tipo: TipoTitulo,
    codigos_alvo: Iterable[str] | None,
    cnpjs_alvo: Iterable[str] | None,
    cancelar: Callable[[], None] | None,
) -> tuple[set[str], set[str]]:
    """Identifica chaves e aliases do SECURIT relacionadas ao ticker."""
    codigos = _codigos_alvo(codigos_alvo)
    cnpjs = _cnpjs_alvo(cnpjs_alvo)
    alvos = _alvos_texto(codigos, cnpjs)
    if not alvos:
        return set(), set()
    chaves: set[str] = set()
    aliases = set(alvos)
    for nome in sorted(csvs):
        if classe_csv(nome) is None:
            continue
        for linha in linhas_contendo(csvs[nome], alvos, cancelar):
            chave = chave_linha(linha, tipo)
            if not chave:
                continue
            chaves.add(chave)
            aliases.update(_aliases_linha(linha))
    return chaves, aliases


def linhas_contendo(
    conteudo: bytes,
    alvos: set[str],
    cancelar: Callable[[], None] | None,
) -> Iterator[LinhaNormalizada]:
    """Itera apenas as linhas brutas que contêm algum dos alvos."""
    linhas = conteudo.splitlines()
    if not linhas:
        return
    colunas = _colunas_csv(linhas[0])
    padrao = _padrao_busca(alvos)
    if not colunas or padrao is None:
        return
    for indice, bruta in enumerate(linhas[1:]):
        checar_cancelamento(cancelar, indice)
        linha = _linha_casada(bruta, colunas, padrao)
        if linha is not None:
            yield linha


def _padrao_busca(alvos: set[str]) -> re.Pattern[bytes] | None:
    """Compila os alvos em uma única expressão de busca textual."""
    partes = [re.escape(alvo.upper().encode("latin1")) for alvo in alvos if alvo]
    if not partes:
        return None
    return re.compile(b"|".join(partes))


def _linha_casada(
    bruta: bytes, colunas: list[str], padrao: re.Pattern[bytes]
) -> LinhaNormalizada | None:
    """Retorna a linha quando ela contém algum alvo, ou ``None``."""
    if not bruta or padrao.search(bruta.upper()) is None:
        return None
    return _linha_csv(bruta, colunas)


def checar_cancelamento(
    cancelar: Callable[[], None] | None, indice: int
) -> None:
    """Observa o cancelamento a cada mil linhas processadas."""
    if cancelar is not None and indice % 1000 == 0:
        cancelar()


def _codigos_alvo(codigos: Iterable[str] | None) -> set[str]:
    """Normaliza os códigos CETIP/ISIN usados no filtro do ticker."""
    return {
        codigo
        for item in (codigos or ())
        if (codigo := codigo_cetip(item))
    }


def _cnpjs_alvo(cnpjs: Iterable[str] | None) -> set[str]:
    """Normaliza e valida os CNPJs de devedor usados no filtro do ticker."""
    return {
        normalizado
        for item in (cnpjs or ())
        if (normalizado := cnpj_normalizado(item))
    }


def _alvos_texto(codigos: set[str], cnpjs: set[str]) -> set[str]:
    """Monta os textos procurados nas linhas brutas dos CSVs."""
    alvos = set(codigos)
    for cnpj in cnpjs:
        alvos.add(cnpj)
        alvos.add(_cnpj_formatado(cnpj))
    return {alvo for alvo in alvos if alvo}


def _cnpj_formatado(cnpj: str) -> str:
    """Formata um CNPJ de 14 dígitos para a busca textual."""
    digitos = normalizar_cnpj(cnpj)
    if len(digitos) != 14:
        return ""
    return (
        f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
        f"{digitos[8:12]}-{digitos[12:]}"
    )


def _aliases_linha(linha: Mapping[str, str]) -> set[str]:
    """Extrai textos que localizam outras linhas do mesmo título."""
    return {
        texto
        for campo in (*_CAMPOS_IDENTIDADE, "CNPJ_Emissora", "CNPJ_Emissor")
        if (texto := valor(linha, campo)) and len(texto) >= 4
    }


def _colunas_csv(cabecalho: bytes) -> list[str]:
    """Normaliza os nomes das colunas do cabeçalho do CSV."""
    texto = cabecalho.decode("latin1").lstrip("\ufeff")
    leitor = csv.reader([texto], delimiter=";")
    return [normalizar_coluna(nome) for nome in next(leitor, [])]


def _linha_csv(
    bruta: bytes, colunas: list[str]
) -> LinhaNormalizada | None:
    """Retorna a linha bruta como linha normalizada, tolerando lixo."""
    leitor = csv.reader([bruta.decode("latin1")], delimiter=";")
    valores = next(leitor, [])
    if not valores:
        return None
    return LinhaNormalizada(dict(zip(colunas, valores)))
