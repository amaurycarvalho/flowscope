"""Entidade e categorias dos documentos relevantes não estruturados da B3."""

from dataclasses import dataclass
from datetime import date, datetime

#: Códigos das categorias de documentos relevantes da B3, na ordem de consulta.
CATEGORIAS_RELEVANTES = (1, 2, 3, 7)

_CATEGORIAS: dict[int, tuple[str, str]] = {
    1: ("Fato Relevante", "fato-relevante"),
    2: ("Assembleia", "assembleia"),
    3: ("Comunicado ao Mercado", "comunicado"),
    7: ("Relatorio", "relatorio"),
}

_NOMES_POR_SLUG: dict[str, str] = {
    slug: nome for nome, slug in _CATEGORIAS.values()
}


def nome_categoria(codigo: int | str) -> str:
    """Retorna o nome legível da categoria a partir do código da API."""
    return _CATEGORIAS[int(codigo)][0]


def slug_categoria(codigo: int | str) -> str:
    """Retorna o slug de pasta da categoria a partir do código da API."""
    return _CATEGORIAS[int(codigo)][1]


def nome_por_slug(slug: str) -> str | None:
    """Retorna o nome da categoria a partir do slug de pasta, ou ``None``."""
    return _NOMES_POR_SLUG.get(slug)


@dataclass(frozen=True)
class DocumentoRelevante:
    """Documento não estruturado (PDF) listado pelo ``GetReportsRelevants``.

    Contém apenas metadados de aquisição; o texto do PDF não é extraído aqui.
    """

    ticker: str
    id_fnet: str | None
    id_documento: str
    categoria: str
    descricao: str
    data_referencia: date | None
    data_entrega: str
    url: str
    tamanho_bytes: int | None
    data_extracao: datetime
