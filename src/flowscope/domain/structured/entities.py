"""Entidades do domínio de dados estruturados da B3.

Facade que reexporta as entidades agora organizadas por contexto:

- ``proventos``: entidade, provento e documento de provento.
- ``regulatorio``: censuras públicas e condições excepcionais.
- ``noticias``: notícias do Plantão B3.
- ``material_facts``: fatos relevantes, assembleias e avisos.
- ``documentos_relevantes``: PDFs não estruturados e suas categorias.
"""

from flowscope.domain.structured.documentos_relevantes import DocumentoRelevante
from flowscope.domain.structured.material_facts import (
    Assembleia,
    AvisoAcionista,
    AvisoDebenturista,
    DocumentoMaterialFact,
    FatoRelevante,
    _texto_documento,
)
from flowscope.domain.structured.noticias import NoticiaB3
from flowscope.domain.structured.proventos import (
    DocumentoProvento,
    Entidade,
    Provento,
)
from flowscope.domain.structured.regulatorio import (
    CensuraPublica,
    CondicaoExcepcional,
)

__all__ = [
    "Assembleia",
    "AvisoAcionista",
    "AvisoDebenturista",
    "CensuraPublica",
    "CondicaoExcepcional",
    "DocumentoMaterialFact",
    "DocumentoProvento",
    "DocumentoRelevante",
    "Entidade",
    "FatoRelevante",
    "NoticiaB3",
    "Provento",
    "_texto_documento",
]
