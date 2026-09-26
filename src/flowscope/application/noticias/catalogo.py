"""Porta, read-model e caso de uso do catálogo de notícias.

O read-model ``montar_secoes`` reaproveita ``montar_catalogo`` da aplicação de
Documentos para agrupar os itens de cada seção de topo na hierarquia
``ano → mês → categoria``. A leitura do índice e do cache é responsabilidade do
adaptador, que implementa ``NoticiasRepository``.
"""

from pathlib import Path
from typing import Protocol

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import montar_catalogo
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.domain.documents import CatalogoTicker
from flowscope.domain.noticias import (
    SECOES_ORDEM,
    TITULO_NOTICIAS,
    CatalogoNoticias,
    NoticiaArquivo,
    SecaoNoticias,
)


class NoticiasRepository(Protocol):
    """Contrato da leitura do catálogo de notícias em cache."""

    def arquivos(self: "NoticiasRepository") -> list[NoticiaArquivo]:
        """Retorna os itens indexados cujo corpo ainda existe no cache local."""
        ...

    def chave(self: "NoticiasRepository", arquivo: NoticiaArquivo) -> str:
        """Deriva a chave estável do item relativa à raiz de cache."""
        ...


class NoticiasCatalogo(NoticiasRepository, Protocol):
    """Repositório de notícias com as raízes e os stores de conteúdo."""

    @property
    def base_dir(self: "NoticiasCatalogo") -> Path:
        """Retorna a raiz de cache varrida."""
        ...

    @property
    def summary_store(self: "NoticiasCatalogo") -> DocumentSummaryStore:
        """Retorna o store de resumos associado ao catálogo."""
        ...

    @property
    def text_store(self: "NoticiasCatalogo") -> DocumentTextStore:
        """Retorna o store de textos associado ao catálogo."""
        ...


class ConsultarCatalogoNoticiasUseCase:
    """Consulta o catálogo de notícias pelo repositório."""

    def __init__(
        self: "ConsultarCatalogoNoticiasUseCase", repositorio: NoticiasRepository
    ) -> None:
        """Guarda o repositório que lê o cache local."""
        self._repositorio = repositorio

    def arquivos(self: "ConsultarCatalogoNoticiasUseCase") -> list[NoticiaArquivo]:
        """Retorna os itens de notícia em cache."""
        return self._repositorio.arquivos()

    def secoes(self: "ConsultarCatalogoNoticiasUseCase") -> CatalogoNoticias:
        """Retorna as categorias de topo com a hierarquia de cada uma."""
        return montar_secoes(self._repositorio.arquivos())

    def chave(
        self: "ConsultarCatalogoNoticiasUseCase", arquivo: NoticiaArquivo
    ) -> str:
        """Deriva a chave estável do item relativa à raiz de cache."""
        return self._repositorio.chave(arquivo)


def montar_secoes(arquivos: list[NoticiaArquivo]) -> CatalogoNoticias:
    """Agrupa os itens nas seções de topo, na ordem fixa de exibição."""
    return CatalogoNoticias(
        TITULO_NOTICIAS,
        tuple(
            SecaoNoticias(nome, _catalogo_da_secao(nome, arquivos))
            for nome in SECOES_ORDEM
        ),
    )


def _catalogo_da_secao(
    nome: str, arquivos: list[NoticiaArquivo]
) -> CatalogoTicker:
    """Monta o catálogo ano → mês → categoria de uma seção."""
    return montar_catalogo(nome, [a for a in arquivos if a.secao == nome])
