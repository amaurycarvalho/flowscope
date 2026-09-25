"""Fonte adicional de contexto do chat com as notícias do Plantão B3.

Lê as notícias em cache do período e as oferece como uma seção própria do
contexto. Não há filtro por ticker na montagem: a LLM infere o ticker referido
na pergunta e seleciona as notícias relacionadas.
"""

import logging
from collections.abc import Callable
from datetime import date, datetime, timezone

from flowscope.application.chat import FonteContexto
from flowscope.infrastructure.b3.noticias_aquisicao import ESCOPO_NOTICIAS
from flowscope.infrastructure.b3.noticias_catalogo import (
    NoticiaArquivo,
    NoticiasCatalog,
)
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui.charts.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    tem_texto,
    texto_preview,
)

logger = logging.getLogger("flowscope")

#: Título da seção de notícias no prompt do chat.
TITULO_FONTE = "Notícias e informações regulatórias da B3"

#: Teto de caracteres da fonte de notícias no contexto do chat.
TETO_CARACTERES = 12000


def _hoje() -> date:
    """Retorna a data corrente em UTC, usada como período padrão."""
    return datetime.now(timezone.utc).date()


class FonteNoticias:
    """Fornece as notícias em cache como fonte adicional de contexto."""

    def __init__(
        self: "FonteNoticias",
        catalog: NoticiasCatalog | None = None,
        text_store: JsonDocumentTextStore | None = None,
        reference_date_provider: Callable[[], date] | None = None,
        teto: int = TETO_CARACTERES,
    ) -> None:
        """Guarda o catálogo, o store de textos e o período de consulta."""
        self._catalog = catalog or NoticiasCatalog()
        self._text_store = text_store or self._catalog.text_store
        self._reference_date_provider = reference_date_provider or _hoje
        self._teto = teto

    def __call__(self: "FonteNoticias", pergunta: str) -> FonteContexto | None:
        """Monta a fonte de notícias do período, ou ``None`` sem conteúdo."""
        del pergunta  # a relevância por ticker é inferida pela LLM
        try:
            arquivos = self._catalog.arquivos(self._reference_date_provider())
        except Exception:  # cache frio ou falha de leitura não quebra o contexto
            logger.warning("Falha ao montar a fonte de notícias", exc_info=True)
            return None
        texto = self._montar(arquivos)
        if not texto:
            return None
        return FonteContexto(TITULO_FONTE, texto)

    def _montar(self: "FonteNoticias", arquivos: list[NoticiaArquivo]) -> str:
        """Concatena os blocos das notícias respeitando o teto de caracteres."""
        blocos: list[str] = []
        total = 0
        for arquivo in arquivos:
            bloco = self._bloco(arquivo)
            if blocos and total + len(bloco) > self._teto:
                break
            blocos.append(bloco)
            total += len(bloco)
        return "\n\n".join(blocos)[: self._teto]

    def _bloco(self: "FonteNoticias", arquivo: NoticiaArquivo) -> str:
        """Monta o bloco textual de um item com categoria e conteúdo."""
        cabecalho = (
            f"[{arquivo.secao}] {arquivo.nome} — "
            f"{arquivo.data_publicacao} ({arquivo.categoria})"
        )
        corpo = arquivo.long_summary or arquivo.short_summary or self._texto(arquivo)
        if not tem_texto(corpo):
            corpo = "(sem texto disponível)"
        return f"{cabecalho}\n{corpo}"

    def _texto(self: "FonteNoticias", arquivo: NoticiaArquivo) -> str:
        """Lê o texto cacheado da notícia, extraindo do HTML em falta."""
        texto = self._text_store.obter(
            ESCOPO_NOTICIAS, self._catalog.chave(arquivo)
        )
        if texto is not None:
            return texto
        return texto_preview(arquivo.caminho, SELETOR_CONTEUDO_DETALHE)
