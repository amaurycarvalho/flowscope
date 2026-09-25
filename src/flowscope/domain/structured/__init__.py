"""Domínio de dados estruturados da B3 com entidades e objetos de valor."""

from flowscope.domain.structured.documentos_relevantes import (
    CATEGORIAS_RELEVANTES,
    DocumentoRelevante,
    nome_categoria,
    nome_por_slug,
    slug_categoria,
)
from flowscope.domain.structured.entities import (
    Assembleia,
    AvisoAcionista,
    AvisoDebenturista,
    CensuraPublica,
    CondicaoExcepcional,
    DocumentoMaterialFact,
    DocumentoProvento,
    Entidade,
    FatoRelevante,
    NoticiaB3,
    ProgramaAquisicao,
    Provento,
)
from flowscope.domain.structured.value_objects import (
    CNPJ,
    ISIN,
    CategoriaDocumento,
    CategoriaMaterialFact,
    CodeCVM,
    ValorProvento,
)

__all__ = [
    "CATEGORIAS_RELEVANTES",
    "CNPJ",
    "ISIN",
    "Assembleia",
    "AvisoAcionista",
    "AvisoDebenturista",
    "CategoriaDocumento",
    "CategoriaMaterialFact",
    "CensuraPublica",
    "CodeCVM",
    "CondicaoExcepcional",
    "DocumentoMaterialFact",
    "DocumentoProvento",
    "DocumentoRelevante",
    "Entidade",
    "FatoRelevante",
    "NoticiaB3",
    "ProgramaAquisicao",
    "Provento",
    "ValorProvento",
    "nome_categoria",
    "nome_por_slug",
    "slug_categoria",
]
