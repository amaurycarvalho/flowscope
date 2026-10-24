"""Join dos títulos do SECURIT com FRE e carteira de FII."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from flowscope.domain.renda_fixa import TituloRendaFixa, cnpj_valido
from flowscope.infrastructure.cvm.renda_fixa_common import codigo_cetip

#: Campos copiados do SECURIT para o título enriquecido.
_CAMPOS_ENRIQUECIMENTO = (
    "emissor_legal",
    "cnpj_emissor",
    "devedor",
    "cnpj_devedor",
    "garantias",
    "coobrigacao",
    "lastro",
    "sobrecolateralizacao",
    "subordinacao",
    "situacao",
    "rating",
    "contingencias",
    "impacto",
    "desempenho",
    "ltv",
    "data_ltv",
)


def indice_securit(
    registro: TituloRendaFixa | list[TituloRendaFixa],
) -> dict[str, TituloRendaFixa]:
    """Indexa os títulos do SECURIT por CETIP/ISIN e por CNPJ de devedor válido."""
    itens = registro if isinstance(registro, list) else [registro]
    indice: dict[str, TituloRendaFixa] = {}
    for item in itens:
        for chave in _chaves_join(item):
            indice.setdefault(chave, item)
    return indice


def enriquecer(
    titulo: TituloRendaFixa, indice: Mapping[str, TituloRendaFixa]
) -> TituloRendaFixa:
    """Aplica os dados do SECURIT ao título, casando por código ou devedor."""
    encontrado = _buscar(indice, titulo)
    if encontrado is None:
        return titulo
    campos = {
        campo: getattr(encontrado, campo)
        for campo in _CAMPOS_ENRIQUECIMENTO
        if getattr(titulo, campo) is None and getattr(encontrado, campo) is not None
    }
    return replace(titulo, **campos) if campos else titulo


def _chaves_join(titulo: TituloRendaFixa) -> list[str]:
    """Lista as chaves de casamento de um título do SECURIT."""
    codigos = list(titulo.codigos) or [codigo_cetip(titulo.identificacao)]
    return [
        chave
        for chave in (
            *codigos,
            titulo.chave_fonte,
            titulo.cnpj_devedor if cnpj_valido(titulo.cnpj_devedor) else None,
        )
        if chave
    ]


def _buscar(
    indice: Mapping[str, TituloRendaFixa], titulo: TituloRendaFixa
) -> TituloRendaFixa | None:
    """Busca o SECURIT pelo código do título e, como fallback, pelo devedor."""
    codigos = list(titulo.codigos) or [codigo_cetip(titulo.identificacao)]
    candidatos = (
        *codigos,
        titulo.chave_fonte,
        titulo.cnpj_devedor if cnpj_valido(titulo.cnpj_devedor) else None,
    )
    for candidato in candidatos:
        if candidato and candidato in indice:
            return indice[candidato]
    return None
