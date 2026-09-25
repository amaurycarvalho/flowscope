"""Fonte de contexto do chat com as notícias do Plantão B3 e da RFC-004.

A fonte opera em **duas camadas**. Na primeira, monta um **índice compacto** de
todos os itens em cache — seção, data, tipo, título e uma chave curta — cobrindo
as quatro categorias e priorizando os itens mais recentes de cada uma, para
caber no orçamento de contexto. Na segunda, atende às chaves que a LLM pedir,
devolvendo o resumo e/ou o texto resolvido do item; notícias "Geral" cujo
documento vinculado (CVM RAD/FNET) não foi baixado são sinalizadas em vez de
apresentar a URL como conteúdo.

Não há filtro por ticker na montagem: a LLM infere o ticker referido na pergunta
e seleciona as notícias relacionadas.
"""

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from itertools import zip_longest
from pathlib import Path

from flowscope.application.chat import FonteContexto
from flowscope.infrastructure.b3.noticias_aquisicao import (
    ESCOPO_NOTICIAS,
    SECAO_GERAL,
    SECOES_ORDEM,
    data_noticia,
)
from flowscope.infrastructure.b3.noticias_catalogo import (
    NoticiaArquivo,
    NoticiasCatalog,
)
from flowscope.infrastructure.b3.noticias_vinculo import apontador_pendente
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui.charts.document_preview import (
    SELETOR_CONTEUDO_DETALHE,
    tem_texto,
    texto_preview,
)

logger = logging.getLogger("flowscope")

#: Título da seção de notícias no prompt do chat.
TITULO_FONTE = "Notícias e informações regulatórias da B3"

#: Instrução de como pedir o conteúdo integral das notícias indexadas.
INSTRUCAO_CHAVES = (
    "As notícias abaixo estão indexadas (seção, data, tipo, título e chave). "
    'Para ler o conteúdo integral de uma delas, inclua a sua chave no campo '
    '"documentos" da resposta.'
)

#: Teto de caracteres do índice compacto de notícias no contexto do chat.
TETO_INDICE = 32000

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


def _chave_curta(chave: str) -> str:
    """Deriva uma chave curta e estável a partir da chave relativa do item."""
    return "n" + hashlib.sha1(chave.encode("utf-8")).hexdigest()[:10]


def _ordem_data(valor: str) -> date:
    """Interpreta a data de publicação para ordenação, tolerando formatos."""
    return data_noticia(valor, date.min)


@dataclass(frozen=True)
class NoticiaEscopo:
    """Notícia em cache com a chave curta usada no escalonamento do chat."""

    secao: str
    nome: str
    data_publicacao: str
    categoria: str
    chave: str
    caminho: Path
    short_summary: str | None = None
    long_summary: str | None = None

    @property
    def chave_curta(self: "NoticiaEscopo") -> str:
        """Chave curta e estável exibida no índice e pedida pela LLM."""
        return _chave_curta(self.chave)


class FonteNoticias:
    """Oferece o índice das notícias e o conteúdo integral sob demanda."""

    def __init__(
        self: "FonteNoticias",
        catalog: NoticiasCatalog | None = None,
        text_store: JsonDocumentTextStore | None = None,
        reference_date_provider: Callable[[], date] | None = None,
        teto: int = TETO_INDICE,
        teto_item: int = TETO_ITEM,
        teto_leitura: int = TETO_LEITURA,
    ) -> None:
        """Guarda o catálogo, o store de textos e os limites do orçamento."""
        self._catalog = catalog or NoticiasCatalog()
        self._text_store = text_store or self._catalog.text_store
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
            arquivos = self._catalog.arquivos(self._reference_date_provider())
        except Exception:  # cache frio ou falha de leitura não quebra o contexto
            logger.warning("Falha ao listar as notícias do chat", exc_info=True)
            return []
        return [self._escopo(arquivo) for arquivo in arquivos]

    def _escopo(self: "FonteNoticias", arquivo: NoticiaArquivo) -> NoticiaEscopo:
        """Monta o escopo do chat a partir de um arquivo do catálogo."""
        return NoticiaEscopo(
            secao=arquivo.secao,
            nome=arquivo.nome,
            data_publicacao=arquivo.data_publicacao,
            categoria=arquivo.categoria,
            chave=self._catalog.chave(arquivo),
            caminho=arquivo.caminho,
            short_summary=arquivo.short_summary,
            long_summary=arquivo.long_summary,
        )

    def _montar(self: "FonteNoticias", escopos: list[NoticiaEscopo]) -> str:
        """Monta o índice compacto respeitando o teto de caracteres."""
        linhas: list[str] = []
        total = len(INSTRUCAO_CHAVES) + 1
        for escopo in _intercalar(escopos):
            linha = self._linha(escopo)
            if linhas and total + len(linha) + 1 > self._teto:
                break
            linhas.append(linha)
            total += len(linha) + 1
        return "\n".join([INSTRUCAO_CHAVES, *linhas])[: self._teto]

    @staticmethod
    def _linha(escopo: NoticiaEscopo) -> str:
        """Formata uma linha do índice com seção, data, tipo, título e chave."""
        return (
            f"[{escopo.secao}] {escopo.data_publicacao} — {escopo.categoria} — "
            f"{escopo.nome} (chave: {escopo.chave_curta})"
        )

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


def _intercalar(escopos: list[NoticiaEscopo]) -> list[NoticiaEscopo]:
    """Ordena por seção (ordem fixa) e intercala, do mais recente ao mais antigo.

    A intercalação garante que todas as categorias apareçam no índice mesmo com
    orçamento curto, em vez de concentrar tudo na primeira seção.
    """
    por_secao = _agrupar_por_secao(escopos)
    filas = [por_secao[secao] for secao in _ordem_secoes(por_secao)]
    return [
        escopo
        for rodada in zip_longest(*filas)
        for escopo in rodada
        if escopo is not None
    ]


def _agrupar_por_secao(
    escopos: list[NoticiaEscopo],
) -> dict[str, list[NoticiaEscopo]]:
    """Agrupa os escopos por seção, ordenando cada grupo do mais recente."""
    por_secao: dict[str, list[NoticiaEscopo]] = {}
    for escopo in escopos:
        por_secao.setdefault(escopo.secao, []).append(escopo)
    for lista in por_secao.values():
        lista.sort(key=lambda e: _ordem_data(e.data_publicacao), reverse=True)
    return por_secao


def _ordem_secoes(por_secao: dict[str, list[NoticiaEscopo]]) -> list[str]:
    """Ordena as seções pela ordem fixa, deixando as desconhecidas ao final."""
    fixas = [secao for secao in SECOES_ORDEM if secao in por_secao]
    extras = [secao for secao in por_secao if secao not in SECOES_ORDEM]
    return fixas + extras
