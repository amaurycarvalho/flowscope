"""Ramo ``/noticias`` da árvore de conhecimento com as notícias em cache.

Expõe os quatro grupos fixos, um índice compacto por grupo e, para cada item
recuperável, os nós de título, resumo e texto. A seleção de relevância fica a
cargo da própria LLM, por navegação (``listar``/``buscar``); não há filtro
determinístico por pergunta nem confirmação de envio. Tudo é lido apenas do
cache local, sem consultar a B3 nem extrair conteúdo sob demanda.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date, datetime, timezone

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    tem_texto,
    texto_preview,
)
from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.noticias.catalogo import NoticiasCatalogo
from flowscope.application.noticias.fonte_chat import (
    TETO_INDICE,
    NoticiaEscopo,
    escopo_de,
    montar_indice,
)
from flowscope.domain.noticias import (
    ESCOPO_NOTICIAS,
    SECAO_GERAL,
    SECOES_ORDEM,
    apontador_pendente,
)

logger = logging.getLogger("flowscope")

#: Teto de caracteres por nó de conteúdo de notícia.
TETO_ITEM = 12000


def _hoje() -> date:
    """Retorna a data corrente em UTC, usada como período padrão."""
    return datetime.now(timezone.utc).date()


class FonteNoticias:
    """Provedor do ramo ``/noticias`` a partir do catálogo em cache."""

    def __init__(
        self: FonteNoticias,
        catalog: NoticiasCatalogo | None = None,
        text_store: DocumentTextStore | None = None,
        reference_date_provider: Callable[[], date] | None = None,
        teto: int = TETO_INDICE,
        teto_item: int = TETO_ITEM,
    ) -> None:
        """Guarda o catálogo, o store de textos e os tetos do índice e dos itens."""
        self._catalog = catalog
        self._text_store = text_store or (
            catalog.text_store if catalog is not None else None
        )
        self._reference_date_provider = reference_date_provider or _hoje
        self._teto = teto
        self._teto_item = teto_item

    def construir(self: FonteNoticias) -> No:
        """Constrói o ramo ``/noticias`` com grupos, índices e itens."""
        raiz = no_interno("/noticias", "noticias")
        raiz.filho(self._grupos())
        escopos = self.listar_recuperaveis()
        for secao in SECOES_ORDEM:
            do_grupo = [e for e in escopos if e.secao == secao]
            if do_grupo:
                raiz.filho(self._ramo_grupo(secao, do_grupo))
        return raiz

    @staticmethod
    def _grupos() -> No:
        """Monta o nó ``/noticias/grupos`` com os quatro grupos fixos."""
        grupos = no_interno("/noticias/grupos", "grupos")
        for secao in SECOES_ORDEM:
            grupos.filho(
                no_folha(
                    f"/noticias/grupos/{secao}",
                    secao,
                    conteudo=secao,
                    campos={"grupo": secao},
                )
            )
        return grupos

    def _ramo_grupo(
        self: FonteNoticias, secao: str, escopos: list[NoticiaEscopo]
    ) -> No:
        """Monta o nó de um grupo com o índice e os itens recuperáveis."""
        grupo = no_interno(f"/noticias/{secao}", secao)
        indice = montar_indice(escopos, self._teto)
        grupo.filho(
            no_folha(
                f"/noticias/{secao}/indice",
                "indice",
                conteudo=indice,
                campos={"indice": indice},
            )
        )
        for escopo in escopos:
            grupo.filho(self._ramo_item(secao, escopo))
        return grupo

    def _ramo_item(
        self: FonteNoticias, secao: str, escopo: NoticiaEscopo
    ) -> No:
        """Monta o nó de uma notícia com título, resumo e texto recuperáveis."""
        base = f"/noticias/{secao}/{escopo.chave_curta}"
        item = no_interno(base, escopo.chave_curta)
        item.filho(
            no_folha(f"{base}/titulo", "titulo", conteudo=escopo.nome, campos={"titulo": escopo.nome})
        )
        resumo = escopo.long_summary or escopo.short_summary
        if resumo:
            item.filho(
                no_folha(
                    f"{base}/resumo",
                    "resumo",
                    conteudo=resumo[: self._teto_item],
                    campos={"resumo": resumo[: self._teto_item]},
                )
            )
        item.filho(
            no_folha(
                f"{base}/texto",
                "texto",
                carregar=lambda e=escopo: (self._conteudo(e) or "")[: self._teto_item],
                campo_pesado="texto",
            )
        )
        return item

    def listar(self: FonteNoticias) -> list[NoticiaEscopo]:
        """Lista as notícias em cache como escopos, tolerando falha de leitura."""
        if self._catalog is None:
            return []
        try:
            arquivos = self._catalog.arquivos()
        except Exception:
            logger.warning("Falha ao listar as notícias do chat", exc_info=True)
            return []
        return [escopo_de(arquivo, self._catalog.chave(arquivo)) for arquivo in arquivos]

    def listar_recuperaveis(self: FonteNoticias) -> list[NoticiaEscopo]:
        """Lista apenas os escopos com resumo ou texto em cache."""
        return [escopo for escopo in self.listar() if self._recuperavel(escopo)]

    def _recuperavel(self: FonteNoticias, escopo: NoticiaEscopo) -> bool:
        """Indica se o item tem resumo ou texto utilizável no cache local."""
        if escopo.short_summary or escopo.long_summary:
            return True
        return bool(self._conteudo(escopo))

    def _conteudo(self: FonteNoticias, escopo: NoticiaEscopo) -> str:
        """Obtém o texto do item apenas do cache local."""
        if self._text_store is None:
            return ""
        texto = self._text_store.obter(ESCOPO_NOTICIAS, escopo.chave)
        if not tem_texto(texto):
            return ""
        if escopo.secao == SECAO_GERAL and self._pendente(escopo, texto):
            return ""
        return texto

    @staticmethod
    def _pendente(escopo: NoticiaEscopo, texto: str) -> bool:
        """Indica se o texto é o apontador da "Geral" ainda não resolvido."""
        corpo = texto_preview(escopo.caminho, SELETOR_CONTEUDO_DETALHE)
        return apontador_pendente(texto, corpo)
