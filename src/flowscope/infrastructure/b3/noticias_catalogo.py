"""Catálogo das notícias em cache para exibição e contexto do chat.

Lê apenas o cache local: os metadados das notícias são indexados pela aquisição
(:class:`NoticiasIndexStore`) e aqui combinados com o conteúdo HTML, os resumos
e os textos já gravados. A leitura não consulta a B3 — a carga de novos itens
ocorre somente pelo botão "Atualizar" da sub-aba. As entidades e a montagem das
seções vêm do domínio e da aplicação; este módulo é o adaptador que varre o
índice e prepara a data ordenável.
"""

import logging
from datetime import date
from pathlib import Path

from flowscope.application.documentos.catalogo import chave_documento
from flowscope.application.noticias.catalogo import montar_secoes
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.noticias import (
    TITULO_NOTICIAS,
    CatalogoNoticias,
    NoticiaArquivo,
    SecaoNoticias,
)
from flowscope.infrastructure.b3.noticias_aquisicao import (
    ESCOPO_NOTICIAS,
    NoticiasCache,
    data_noticia,
)
from flowscope.infrastructure.b3.noticias_index import NoticiasIndexStore
from flowscope.infrastructure.b3.noticias_shards import (
    NoticiasSummaryStore,
    NoticiasTextStore,
)

logger = logging.getLogger("flowscope")

__all__ = [
    "TITULO_NOTICIAS",
    "CatalogoNoticias",
    "NoticiaArquivo",
    "NoticiasCatalog",
    "SecaoNoticias",
]


class NoticiasCatalog:
    """Lê o catálogo de notícias a partir do índice e do cache local.

    Adaptador de filesystem da porta ``NoticiasRepository``: localiza os itens e
    delega a montagem das seções ao read-model da aplicação.
    """

    def __init__(
        self: "NoticiasCatalog",
        cache_dir: Path | None = None,
        index_store: NoticiasIndexStore | None = None,
    ) -> None:
        """Inicializa o catálogo com a raiz de cache e o índice de metadados."""
        self._cache = NoticiasCache(cache_dir)
        self._index = index_store or NoticiasIndexStore(
            cache_dir=self._cache.base_dir
        )
        self._summary_store = NoticiasSummaryStore(
            cache_dir=self._cache.base_dir
        )
        self._text_store = NoticiasTextStore(cache_dir=self._cache.base_dir)

    @property
    def base_dir(self: "NoticiasCatalog") -> Path:
        """Retorna a raiz de cache varrida."""
        return self._cache.base_dir

    @property
    def cache(self: "NoticiasCatalog") -> NoticiasCache:
        """Retorna o cache de notícias associado ao catálogo."""
        return self._cache

    @property
    def summary_store(self: "NoticiasCatalog") -> NoticiasSummaryStore:
        """Retorna o store de resumos associado ao catálogo."""
        return self._summary_store

    @property
    def text_store(self: "NoticiasCatalog") -> NoticiasTextStore:
        """Retorna o store de textos associado ao catálogo."""
        return self._text_store

    def chave(self: "NoticiasCatalog", arquivo: NoticiaArquivo) -> str:
        """Deriva a chave estável do item relativa à raiz de cache."""
        return chave_documento(arquivo.caminho, self._cache.base_dir)

    def secoes(
        self: "NoticiasCatalog",
        reference_date: date | None = None,
        palavra: str | None = None,
    ) -> CatalogoNoticias:
        """Retorna as categorias de topo com a hierarquia de cada uma.

        O período e o termo são aceitos por compatibilidade de assinatura e não
        filtram: o catálogo lê o cache local completo, sem consultar a B3.
        """
        del reference_date, palavra
        return montar_secoes(self.arquivos())

    def arquivos(
        self: "NoticiasCatalog",
        reference_date: date | None = None,
        palavra: str | None = None,
    ) -> list[NoticiaArquivo]:
        """Retorna os itens indexados cujo corpo ainda existe no cache local.

        O período e o termo são aceitos por compatibilidade de assinatura e não
        filtram: a leitura é somente do cache local.
        """
        del reference_date, palavra
        resumos = self._summary_store.resumos(ESCOPO_NOTICIAS)
        arquivos: list[NoticiaArquivo] = []
        for relativo, meta in self._index.itens().items():
            caminho = self._cache.base_dir / relativo
            if not caminho.is_file():
                continue
            ano, mes = _ano_mes_do_relativo(relativo)
            resumo = resumos.get(relativo)
            arquivos.append(
                NoticiaArquivo(
                    ticker=ESCOPO_NOTICIAS,
                    ano=ano,
                    mes=mes,
                    categoria=meta.categoria or "—",
                    nome=meta.titulo or caminho.name,
                    tipo="html",
                    caminho=caminho,
                    short_summary=_texto(resumo, "short_summary"),
                    long_summary=_texto(resumo, "long_summary"),
                    url=meta.url,
                    data_publicacao=meta.data_publicacao,
                    secao=meta.secao,
                    data_ordinal=_ordinal(meta.data_publicacao, ano, mes),
                )
            )
        return arquivos


def _ordinal(data_publicacao: str, ano: int, mes: int) -> int:
    """Interpreta a data de publicação como ordinal, com fallback ``(ano, mês)``."""
    ano_base = max(ano, 1)
    mes_base = mes if 1 <= mes <= 12 else 1
    return data_noticia(data_publicacao, date(ano_base, mes_base, 1)).toordinal()


def _ano_mes_do_relativo(relativo: str) -> tuple[int, int]:
    """Extrai ``(ano, mês)`` de ``noticias/<AAAA>/<MM>/<hash>.html``."""
    partes = Path(relativo).parts
    if len(partes) < 3:
        return 0, 0
    try:
        return int(partes[-3]), int(partes[-2])
    except ValueError:
        return 0, 0


def _texto(resumo: ResumoDocumento | None, atributo: str) -> str | None:
    """Extrai um campo de resumo, tolerando ausência."""
    if resumo is None:
        return None
    return getattr(resumo, atributo, None)
