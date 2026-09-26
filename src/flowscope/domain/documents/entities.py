"""Entidades imutáveis do catálogo de documentos em cache.

A hierarquia é ``ticker → ano → mês → categoria → arquivo``. As entidades são
somente leitura e não dependem de infraestrutura: descrevem o que o catálogo
contém, não como os arquivos foram encontrados.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class DocumentoArquivo:
    """Arquivo de documento em cache."""

    ticker: str
    ano: int
    mes: int
    categoria: str
    nome: str
    tipo: str
    caminho: Path
    short_summary: str | None = None
    long_summary: str | None = None


@dataclass(frozen=True)
class CategoriaDocumentos:
    """Categoria de documentos com seus arquivos, do mais recente ao mais antigo."""

    nome: str
    arquivos: tuple[DocumentoArquivo, ...] = ()


@dataclass(frozen=True)
class MesDocumentos:
    """Mês com as categorias de documentos encontradas."""

    mes: int
    categorias: tuple[CategoriaDocumentos, ...] = ()


@dataclass(frozen=True)
class AnoDocumentos:
    """Ano com os meses de documentos encontrados."""

    ano: int
    meses: tuple[MesDocumentos, ...] = ()


@dataclass(frozen=True)
class CatalogoTicker:
    """Catálogo hierárquico dos documentos em cache de um ticker."""

    ticker: str
    anos: tuple[AnoDocumentos, ...] = field(default_factory=tuple)

    @property
    def vazio(self: "CatalogoTicker") -> bool:
        """Indica se o ticker não possui documentos em cache."""
        return not self.anos
