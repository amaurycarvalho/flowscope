"""Orquestração da carga (aquisição) das notícias do Plantão B3.

Baixa o corpo dos itens das quatro fontes, tolerando falhas por fonte e por
item, reporta progresso e persiste o índice em lotes. A "Geral" é carregada dia
a dia, pulando os dias já processados; as fontes regulatórias são carregadas
item a item. As fontes, a conversão e o cache vivem em ``noticias_aquisicao``.
"""

import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.structured_ports import RegulacaoRepository
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.noticias_aquisicao import (
    _LOTE_INDICE,
    SECAO_GERAL,
    ItemNoticia,
    NoticiasCache,
    baixar_noticia,
    chave_item,
    data_noticia,
    fontes_noticias,
    html_do_item,
    itens_de_janela,
    janelas_geral,
)
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")


class AquisicaoNoticias:
    """Adquire e cacheia o corpo dos artigos das notícias do Plantão B3."""

    def __init__(
        self: "AquisicaoNoticias",
        repository: RegulacaoRepository | None = None,
        cache: CacheManager | None = None,
        baixar: Callable[[str], bytes | None] | None = None,
    ) -> None:
        """Inicializa o orquestrador com repositório, cache e download injetável."""
        self._repository = repository or B3FundosClient(cache=cache)
        self._cache = NoticiasCache(cache.get_cache_dir() if cache else None)
        self._index = NoticiasIndexStore(cache_dir=self._cache.base_dir)
        self._baixar = baixar or baixar_noticia

    @property
    def cache(self: "AquisicaoNoticias") -> NoticiasCache:
        """Retorna o cache de notícias associado à aquisição."""
        return self._cache

    def adquirir(
        self: "AquisicaoNoticias",
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancel_token: CancellationToken | None = None,
        palavra: str | None = None,
    ) -> None:
        """Baixa e grava o corpo dos itens, fonte a fonte, tolerando falhas.

        O status de cada categoria é anunciado antes da listagem e o progresso
        é reportado por item (fontes regulatórias) ou por dia ("Geral"). A
        "Geral" só relê os dias ainda não processados, exceto o primeiro (mais
        recente), sempre recarregado. ``cancel_token`` é observado no topo de
        cada unidade de trabalho.
        """
        for secao, listar in fontes_noticias(self._repository, reference_date, palavra):
            if secao == SECAO_GERAL:
                self._adquirir_geral(reference_date, palavra, progress, cancel_token)
            else:
                self._adquirir_fonte(
                    secao, listar, reference_date, progress, cancel_token
                )

    def _adquirir_fonte(
        self: "AquisicaoNoticias",
        secao: str,
        listar: Callable[[], list[ItemNoticia]],
        reference_date: date,
        progress: Callable[[int, int, str], None] | None,
        cancel_token: CancellationToken | None,
    ) -> None:
        """Baixa e indexa os itens de uma fonte regulatória, item a item.

        As escritas do índice são agrupadas a cada ``_LOTE_INDICE`` itens e ao
        final, evitando regravar o índice a cada item.
        """
        self._anunciar(progress, secao)
        itens = listar()
        total = len(itens)
        self._reportar(progress, 0, total, secao)
        pendentes: list[tuple[Path, NoticiaMeta]] = []
        try:
            for atual, item in enumerate(itens, start=1):
                if cancel_token is not None:
                    cancel_token.raise_if_cancelled()
                registro = self._persistir(item, reference_date)
                if registro is not None:
                    pendentes.append(registro)
                if len(pendentes) >= _LOTE_INDICE:
                    self._index.registrar_muitos(pendentes)
                    pendentes = []
                self._reportar(progress, atual, total, secao)
        finally:
            if pendentes:
                self._index.registrar_muitos(pendentes)

    def _adquirir_geral(
        self: "AquisicaoNoticias",
        reference_date: date,
        palavra: str | None,
        progress: Callable[[int, int, str], None] | None,
        cancel_token: CancellationToken | None,
    ) -> None:
        """Baixa e indexa a "Geral" dia a dia, pulando os dias já processados.

        As escritas do índice (itens e marcadores) são agrupadas a cada
        ``_LOTE_INDICE`` dias e ao final. Em cancelamento, os itens já
        processados são indexados sem marcar o dia, para que ele seja retomado.
        """
        self._anunciar(progress, SECAO_GERAL)
        mais_antiga, referencia = self._index.geral_processada()
        janelas = janelas_geral(reference_date, mais_antiga, referencia)
        total = len(janelas)
        self._reportar(progress, 0, total, SECAO_GERAL)
        registros: list[tuple[Path, NoticiaMeta]] = []
        mais_antiga_pendente: date | None = None
        referencia_pendente: date | None = None
        desde_flush = 0
        try:
            for indice, (inicio, fim) in enumerate(janelas, start=1):
                if cancel_token is not None:
                    cancel_token.raise_if_cancelled()
                itens = itens_de_janela(self._repository, inicio, fim, palavra)
                if itens is None:
                    break  # dia não processado; retoma daqui na próxima carga
                for item in itens:
                    if cancel_token is not None:
                        cancel_token.raise_if_cancelled()
                    registro = self._persistir(item, reference_date)
                    if registro is not None:
                        registros.append(registro)
                mais_antiga_pendente = inicio  # do mais recente ao mais antigo
                if indice == 1:
                    referencia_pendente = reference_date
                desde_flush += 1
                if desde_flush >= _LOTE_INDICE:
                    self._flush_geral(
                        registros, mais_antiga_pendente, referencia_pendente
                    )
                    registros = []
                    referencia_pendente = None
                    desde_flush = 0
                self._reportar(progress, indice, total, SECAO_GERAL)
        except OperacaoCancelada:
            self._index.registrar_lote(registros)  # preserva sem marcar o dia
            raise
        self._flush_geral(registros, mais_antiga_pendente, referencia_pendente)

    def _flush_geral(
        self: "AquisicaoNoticias",
        registros: list[tuple[Path, NoticiaMeta]],
        mais_antiga: date | None,
        referencia: date | None,
    ) -> None:
        """Grava itens e marcadores da "Geral" em uma única passagem."""
        if not registros and mais_antiga is None:
            return
        self._index.registrar_lote(
            registros,
            geral_mais_antiga=mais_antiga,
            geral_referencia=referencia,
        )

    def _persistir(
        self: "AquisicaoNoticias", item: ItemNoticia, fallback: date
    ) -> tuple[Path, NoticiaMeta] | None:
        """Grava o conteúdo do item e indexa os seus metadados.

        O conteúdo é baixado quando necessário; itens sem corpo (sem URL e sem
        conteúdo próprio) são ignorados. Itens já em cache têm os metadados
        registrados mesmo assim, reparando índices ausentes ou antigos.
        """
        chave = chave_item(item)
        data = data_noticia(item.data_publicacao, fallback)
        caminho = self._cache.caminho(chave, data)
        if not self._cache.existe(chave, data):
            conteudo = self._conteudo(item)
            if not conteudo:
                return None
            self._cache.gravar(chave, data, conteudo)
        return caminho, NoticiaMeta(
            secao=item.secao,
            titulo=item.titulo,
            data_publicacao=item.data_publicacao,
            categoria=item.categoria,
            url=item.url,
        )

    def _conteudo(self: "AquisicaoNoticias", item: ItemNoticia) -> bytes | None:
        """Obtém o corpo do item, do download ou do próprio conteúdo.

        Itens sem URL e sem conteúdo próprio (notícias do Plantão B3 sem link)
        são ignorados; itens regulatórios trazem o próprio conteúdo.
        """
        url = (item.url or "").strip()
        if url:
            try:
                return self._baixar(url)
            except Exception:  # falha de rede isolada por item
                logger.warning("Falha ao baixar notícia %s", url, exc_info=True)
                return None
        if item.conteudo is None:
            return None
        return html_do_item(item)

    @staticmethod
    def _anunciar(
        progress: Callable[[int, int, str], None] | None, secao: str
    ) -> None:
        """Anuncia o início da carga de uma categoria na barra de status."""
        if progress is None:
            return
        progress(0, 1, f"• Carregando {secao}…")

    @staticmethod
    def _reportar(
        progress: Callable[[int, int, str], None] | None,
        current: int,
        total: int,
        secao: str,
    ) -> None:
        """Notifica o progresso por item, identificando a categoria carregada."""
        if progress is None:
            return
        if total > 0:
            label = f"• {secao} ({current}/{total})"
        else:
            label = f"• {secao}…"
        progress(current, total, label)
