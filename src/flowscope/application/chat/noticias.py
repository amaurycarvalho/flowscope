"""Fonte de contexto do chat com as notícias do Plantão B3 e da RFC-004.

A fonte opera em **duas camadas**. Na primeira, monta um **índice compacto** de
todos os itens em cache — seção, data, tipo, título e uma chave curta — cobrindo
as quatro categorias e priorizando os itens mais recentes de cada uma, para
caber no orçamento de contexto. Na segunda, atende às chaves que a LLM pedir,
devolvendo o resumo e/ou o texto resolvido do item; notícias "Geral" cujo
documento vinculado (CVM RAD/FNET) não foi baixado são sinalizadas em vez de
apresentar a URL como conteúdo.

A montagem do índice é regra de aplicação; aqui apenas se injeta o catálogo e o
store de texto e se formata o bloco. Não há filtro por ticker: a LLM infere o
ticker referido na pergunta e seleciona as notícias relacionadas.
"""

import logging
from collections.abc import Callable
from datetime import date, datetime, timezone

from flowscope.application.chat import FonteContexto
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
    apontador_pendente,
)

logger = logging.getLogger("flowscope")

#: Título da seção de notícias no prompt do chat.
TITULO_FONTE = "Notícias e informações regulatórias da B3"

#: Teto de caracteres por notícia lida na segunda camada.
TETO_ITEM = 12000

#: Teto global de caracteres da leitura das notícias na segunda camada.
TETO_LEITURA = 48000

#: Aviso de que o documento vinculado de uma notícia não foi baixado.
SEM_DOCUMENTO = (
    "(Documento vinculado ainda não baixado; selecione a notícia na sub-aba "
    '"Notícias" ou rode "Resumir pendentes" para obtê-lo.)'
)


def _hoje() -> date:
    """Retorna a data corrente em UTC, usada como período padrão."""
    return datetime.now(timezone.utc).date()


class FonteNoticias:
    """Oferece o índice das notícias e o conteúdo integral sob demanda."""

    def __init__(
        self: "FonteNoticias",
        catalog: NoticiasCatalogo | None = None,
        text_store: DocumentTextStore | None = None,
        reference_date_provider: Callable[[], date] | None = None,
        teto: int = TETO_INDICE,
        teto_item: int = TETO_ITEM,
        teto_leitura: int = TETO_LEITURA,
    ) -> None:
        """Guarda o catálogo, o store de textos e os limites do orçamento."""
        self._catalog = catalog
        self._text_store = text_store or (
            catalog.text_store if catalog is not None else None
        )
        self._reference_date_provider = reference_date_provider or _hoje
        self._teto = teto
        self._teto_item = teto_item
        self._teto_leitura = teto_leitura

    # ── Primeira camada: índice compacto ─────────────────────────────

    def __call__(self: "FonteNoticias", pergunta: str) -> FonteContexto | None:
        """Monta o índice compacto das notícias, ou ``None`` sem conteúdo."""
        del pergunta  # a relevância por ticker é inferida pela LLM
        escopos = self.listar()
        if not escopos:
            return None
        return FonteContexto(TITULO_FONTE, self._montar(escopos))

    def listar(self: "FonteNoticias") -> list[NoticiaEscopo]:
        """Lista as notícias em cache como escopos, tolerando falha de leitura."""
        try:
            arquivos = self._catalog.arquivos()
        except Exception:  # cache frio ou falha de leitura não quebra o contexto
            logger.warning("Falha ao listar as notícias do chat", exc_info=True)
            return []
        return [escopo_de(arquivo, self._catalog.chave(arquivo)) for arquivo in arquivos]

    def _montar(self: "FonteNoticias", escopos: list[NoticiaEscopo]) -> str:
        """Monta o índice compacto respeitando o teto de caracteres."""
        return montar_indice(escopos, self._teto)

    # ── Segunda camada: conteúdo integral sob demanda ────────────────

    def resolver_alvos(
        self: "FonteNoticias", chaves: set[str] | list[str]
    ) -> list[NoticiaEscopo]:
        """Resolve as chaves curtas devolvidas pela LLM em escopos."""
        desejadas = {c for c in chaves if c}
        if not desejadas:
            return []
        return [
            escopo
            for escopo in self.listar()
            if escopo.chave_curta in desejadas
        ]

    def preparar_texto(self: "FonteNoticias", alvos: list[NoticiaEscopo]) -> str:
        """Lê o resumo/texto integral dos alvos, aplicando os tetos."""
        blocos: list[str] = []
        total = 0
        for alvo in alvos:
            bloco = self._bloco_conteudo(alvo)
            if len(bloco) > self._teto_item:
                bloco = bloco[: self._teto_item]
            restante = self._teto_leitura - total
            if restante <= 0:
                break
            if len(bloco) > restante:
                bloco = bloco[:restante]
            total += len(bloco)
            blocos.append(bloco)
        return "\n\n".join(blocos)

    def _bloco_conteudo(self: "FonteNoticias", alvo: NoticiaEscopo) -> str:
        """Monta o bloco de uma notícia com o resumo e o texto resolvido."""
        cabecalho = (
            f"### [{alvo.secao}] {alvo.nome} — {alvo.data_publicacao} "
            f"({alvo.categoria})"
        )
        texto = self._conteudo(alvo)
        corpo = alvo.long_summary or alvo.short_summary
        if corpo:
            return f"{cabecalho}\nResumo: {corpo}\nTexto: {texto or SEM_DOCUMENTO}"
        if tem_texto(texto):
            return f"{cabecalho}\n{texto}"
        return f"{cabecalho}\n{SEM_DOCUMENTO}"

    def _conteudo(self: "FonteNoticias", alvo: NoticiaEscopo) -> str:
        """Obtém o texto do item do cache, sinalizando apontador não resolvido."""
        texto = self._text_store.obter(ESCOPO_NOTICIAS, alvo.chave)
        if texto is None:
            texto = texto_preview(alvo.caminho, SELETOR_CONTEUDO_DETALHE)
        if not tem_texto(texto):
            return ""
        if alvo.secao == SECAO_GERAL and self._pendente(alvo, texto):
            return ""
        return texto

    @staticmethod
    def _pendente(alvo: NoticiaEscopo, texto: str) -> bool:
        """Indica se o texto é o apontador da "Geral" ainda não resolvido."""
        corpo = texto_preview(alvo.caminho, SELETOR_CONTEUDO_DETALHE)
        return apontador_pendente(texto, corpo)
