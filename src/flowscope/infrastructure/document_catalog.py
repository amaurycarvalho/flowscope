"""Catálogo dos documentos em cache por ticker, ano, mês e categoria.

Varre as raízes de cache das fontes de documentos — ``bdr/``,
``informe-mensal/`` e ``documentos-relevantes/`` — e normaliza os arquivos
encontrados em uma hierarquia pronta para exibição, delegando o agrupamento e a
ordenação ao read-model da aplicação. A varredura é somente leitura e ignora
raízes inexistentes.
"""

from dataclasses import replace
from pathlib import Path

from flowscope.application.documentos.catalogo import chave_documento, montar_catalogo
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import (
    AnoDocumentos,
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
    MesDocumentos,
)
from flowscope.domain.structured import nome_por_slug
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

__all__ = [
    "AnoDocumentos",
    "CatalogoTicker",
    "CategoriaDocumentos",
    "DocumentCatalog",
    "DocumentoArquivo",
    "MesDocumentos",
    "chave_documento",
    "montar_catalogo",
]

#: Raízes com categoria fixa e o tipo de arquivo esperado.
_RAIZES_FIXAS: tuple[tuple[str, str, str], ...] = (
    ("bdr", "Aviso aos Acionistas", "pdf"),
    ("informe-mensal", "Informe Mensal", "html"),
)

#: Raiz cuja categoria é derivada da subpasta sob o mês.
_RAIZ_DOCUMENTOS_RELEVANTES = "documentos-relevantes"


class DocumentCatalog:
    """Varre as raízes de cache e normaliza os documentos de um ticker.

    Adaptador de filesystem da porta ``CatalogoRepository``: localiza os
    arquivos e delega a montagem da hierarquia ao read-model da aplicação.
    """

    def __init__(
        self: "DocumentCatalog",
        cache_dir: Path | None = None,
        summary_store: JsonDocumentSummaryStore | None = None,
        text_store: JsonDocumentTextStore | None = None,
    ) -> None:
        """Inicializa o catálogo com o diretório raiz e os stores de conteúdo."""
        self._base = (
            Path(cache_dir)
            if cache_dir is not None
            else CacheManager().get_cache_dir()
        )
        self._store = (
            summary_store
            if summary_store is not None
            else JsonDocumentSummaryStore(cache_dir=self._base)
        )
        self._text_store = (
            text_store
            if text_store is not None
            else JsonDocumentTextStore(cache_dir=self._base)
        )

    @property
    def base_dir(self: "DocumentCatalog") -> Path:
        """Retorna o diretório raiz de cache varrido."""
        return self._base

    @property
    def summary_store(self: "DocumentCatalog") -> JsonDocumentSummaryStore:
        """Retorna o store de resumos associado ao catálogo."""
        return self._store

    @property
    def text_store(self: "DocumentCatalog") -> JsonDocumentTextStore:
        """Retorna o store de textos associado ao catálogo."""
        return self._text_store

    def catalogo(self: "DocumentCatalog", ticker: str) -> CatalogoTicker:
        """Retorna o catálogo de documentos em cache do ticker informado."""
        chave = ticker.strip().upper()
        resumos = self._store.resumos(chave)
        arquivos: list[DocumentoArquivo] = []
        for pasta, categoria, tipo in _RAIZES_FIXAS:
            arquivos.extend(
                _varrer_categoria_fixa(
                    self._base / pasta, chave, categoria, tipo
                )
            )
        arquivos.extend(
            _varrer_documentos_relevantes(
                self._base / _RAIZ_DOCUMENTOS_RELEVANTES, chave
            )
        )
        arquivos = [_enriquecer(arquivo, resumos, self._base) for arquivo in arquivos]
        return montar_catalogo(chave, arquivos)


def _enriquecer(
    arquivo: DocumentoArquivo,
    resumos: dict[str, ResumoDocumento],
    base: Path,
) -> DocumentoArquivo:
    """Preenche os resumos do arquivo a partir do mapa do ticker."""
    resumo = resumos.get(chave_documento(arquivo.caminho, base))
    if resumo is None:
        return arquivo
    return replace(
        arquivo,
        short_summary=resumo.short_summary,
        long_summary=resumo.long_summary,
    )


def _varrer_categoria_fixa(
    raiz: Path, ticker: str, categoria: str, tipo: str
) -> list[DocumentoArquivo]:
    """Varre uma raiz ``<ticker>/<AAAA>/<MM>/<id>.<tipo>`` com categoria fixa."""
    pasta = raiz / ticker
    arquivos: list[DocumentoArquivo] = []
    for caminho in pasta.glob(f"*/*/*.{tipo}"):
        if not caminho.is_file():
            continue
        partes = caminho.relative_to(pasta).parts
        if len(partes) != 3:
            continue
        arquivos.append(
            _entrada(caminho, ticker, partes[0], partes[1], categoria, tipo)
        )
    return arquivos


def _varrer_documentos_relevantes(
    raiz: Path, ticker: str
) -> list[DocumentoArquivo]:
    """Varre ``documentos-relevantes/<ticker>/<AAAA>/<MM>/<categoria>/<id>.pdf``."""
    pasta = raiz / ticker
    arquivos: list[DocumentoArquivo] = []
    for caminho in pasta.glob("*/*/*/*.pdf"):
        if not caminho.is_file():
            continue
        partes = caminho.relative_to(pasta).parts
        if len(partes) != 4:
            continue
        categoria = nome_por_slug(partes[2]) or partes[2]
        arquivos.append(
            _entrada(caminho, ticker, partes[0], partes[1], categoria, "pdf")
        )
    return arquivos


def _entrada(
    caminho: Path,
    ticker: str,
    ano: str,
    mes: str,
    categoria: str,
    tipo: str,
) -> DocumentoArquivo:
    """Monta uma entrada de arquivo a partir das partes do caminho."""
    try:
        ano_int = int(ano)
        mes_int = int(mes)
    except ValueError:
        ano_int, mes_int = 0, 0
    return DocumentoArquivo(
        ticker=ticker,
        ano=ano_int,
        mes=mes_int,
        categoria=categoria,
        nome=caminho.name,
        tipo=tipo,
        caminho=caminho,
    )
