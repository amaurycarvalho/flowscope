"""Entidades imutáveis do catálogo de notícias.

A hierarquia de cada seção é a mesma do catálogo de documentos
(``ano → mês → categoria → item``). O item de notícia estende o arquivo de
documento com a URL, a data de publicação e a seção de topo; ``data_ordinal`` é
a data já interpretada pelo adaptador, usada para ordenação pura.
"""

from dataclasses import dataclass, field

from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo


@dataclass(frozen=True)
class NoticiaArquivo(DocumentoArquivo):
    """Item de notícia com corpo em cache, exibível e resumível como documento."""

    url: str | None = None
    data_publicacao: str = ""
    secao: str = ""
    data_ordinal: int = 0


@dataclass(frozen=True)
class SecaoNoticias:
    """Categoria de topo da sub-aba com seu catálogo ano → mês → categoria."""

    nome: str
    catalogo: CatalogoTicker


@dataclass(frozen=True)
class CatalogoNoticias:
    """Catálogo da sub-aba: raiz e categorias de topo em ordem fixa."""

    titulo: str
    secoes: tuple[SecaoNoticias, ...] = field(default_factory=tuple)

    @property
    def vazio(self: "CatalogoNoticias") -> bool:
        """Indica se nenhuma categoria de topo possui itens em cache."""
        return not any(secao.catalogo.anos for secao in self.secoes)
