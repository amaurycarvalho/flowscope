"""Cascata de recuperação de documentos sobre os caches da sub-aba Documentos.

A cascata é estritamente somente-leitura de cache: lê os resumos curtos e longos
do catálogo de documentos e, quando a resposta precisa de mais detalhe, o texto
integral dos documentos-alvo já extraído e em cache. Documentos pendentes de
resumo ou de extração são omitidos em silêncio — nenhum resumo é gerado e nenhum
texto é extraído durante o chat. Antes da leitura do texto integral aplica-se o
gate de confirmação por quantidade e, depois, o orçamento de contexto.
"""

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    chave_documento,
)
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo

logger = logging.getLogger("flowscope")

#: Teto de caracteres por documento enviado à LLM.
TETO_DOCUMENTO = 12000

#: Teto global de caracteres do contexto documental enviado à LLM.
TETO_GLOBAL = 40000

#: Faixas do gate de confirmação por quantidade de documentos-alvo.
FAIXA_AUTOMATICA = "automatica"
FAIXA_LISTAR = "listar"
FAIXA_QUANTIDADE = "quantidade"

#: Assinatura do callback que confirma a leitura do texto integral.
ConfirmaAlvos = Callable[[int, list[str]], bool]


def faixa_confirmacao(quantidade: int) -> str:
    """Classifica a quantidade de alvos na faixa do gate de confirmação.

    Até 3 documentos prossegue automaticamente; de 4 a 7 lista os nomes; com
    8 ou mais informa apenas a quantidade.
    """
    if quantidade <= 3:
        return FAIXA_AUTOMATICA
    if quantidade <= 7:
        return FAIXA_LISTAR
    return FAIXA_QUANTIDADE


@dataclass(frozen=True)
class DocumentoEscopo:
    """Documento do escopo do chat com a sua chave estável e resumos."""

    ticker: str
    nome: str
    categoria: str
    ano: int
    mes: int
    chave: str
    caminho: Path
    short_summary: str | None = None
    long_summary: str | None = None


def _achatar(catalogo: CatalogoTicker) -> list[DocumentoArquivo]:
    """Percorre a hierarquia do catálogo devolvendo os arquivos em ordem."""
    arquivos: list[DocumentoArquivo] = []
    for ano in catalogo.anos:
        for mes in ano.meses:
            for categoria in mes.categorias:
                arquivos.extend(categoria.arquivos)
    return arquivos


class CascataDocumentos:
    """Recupera o contexto documental em cascata para uma pergunta."""

    def __init__(
        self: "CascataDocumentos",
        catalog: CatalogoDocumentos | None = None,
        confirmar: ConfirmaAlvos | None = None,
        teto_documento: int = TETO_DOCUMENTO,
        teto_global: int = TETO_GLOBAL,
    ) -> None:
        """Guarda o catálogo e os limites do orçamento."""
        self._catalog = catalog
        self._confirmar = confirmar
        self._teto_documento = teto_documento
        self._teto_global = teto_global

    def listar(
        self: "CascataDocumentos",
        ticker: str | None,
        watchlist: Iterable[str],
    ) -> list[DocumentoEscopo]:
        """Lista os documentos do escopo, na watchlist ou no ticker foco."""
        tickers = [ticker] if ticker else list(watchlist)
        documentos: list[DocumentoEscopo] = []
        for alvo in tickers:
            if alvo:
                documentos.extend(self._escopo_ticker(alvo))
        return documentos

    def _escopo_ticker(self: "CascataDocumentos", ticker: str) -> list[DocumentoEscopo]:
        """Monta os documentos do escopo a partir do catálogo de um ticker."""
        return [
            DocumentoEscopo(
                ticker=arquivo.ticker,
                nome=arquivo.nome,
                categoria=arquivo.categoria,
                ano=arquivo.ano,
                mes=arquivo.mes,
                chave=self.chave(arquivo),
                caminho=arquivo.caminho,
                short_summary=arquivo.short_summary,
                long_summary=arquivo.long_summary,
            )
            for arquivo in _achatar(self._catalog.catalogo(ticker))
        ]

    def chave(self: "CascataDocumentos", arquivo: DocumentoArquivo) -> str:
        """Deriva a chave estável do documento relativa à raiz de cache."""
        return chave_documento(arquivo.caminho, self._catalog.base_dir)

    def montar_resumos(
        self: "CascataDocumentos",
        ticker: str | None,
        watchlist: Iterable[str],
    ) -> tuple[str, list[DocumentoEscopo]]:
        """Monta o bloco de resumos cacheados do escopo.

        Documentos pendentes de resumo são omitidos em silêncio: nada é gerado
        nem persistido. Devolve o texto e a lista de documentos-alvo candidatos
        (os que têm resumo), para o caso de uso escalar para o texto integral.
        """
        com_resumo = [
            doc
            for doc in self.listar(ticker, watchlist)
            if doc.short_summary or doc.long_summary
        ]
        return self._formatar_resumos(com_resumo), com_resumo

    def _formatar_resumos(self: "CascataDocumentos", documentos: list[DocumentoEscopo]) -> str:
        """Formata os resumos de cada documento identificando a sua chave."""
        blocos: list[str] = []
        for doc in documentos:
            titulo = f"{doc.ticker} — {doc.categoria} — {doc.nome}"
            blocos.append(
                f"### {titulo}\nChave: {doc.chave}\n"
                f"Resumo curto: {doc.short_summary or ''}\n"
                f"Resumo longo: {doc.long_summary or ''}"
            )
        return "\n\n".join(blocos)

    def resolver_alvos(
        self: "CascataDocumentos", chaves: Iterable[str]
    ) -> list[DocumentoEscopo]:
        """Resolve as chaves devolvidas pela LLM em documentos do escopo."""
        desejadas = {c for c in chaves if c}
        if not desejadas:
            return []
        return self._buscar_por_chaves(desejadas)

    def _buscar_por_chaves(
        self: "CascataDocumentos", desejadas: set[str]
    ) -> list[DocumentoEscopo]:
        """Varre o catálogo dos tickers em cache à procura das chaves."""
        encontrados: list[DocumentoEscopo] = []
        for ticker in self._tickers_em_cache():
            for doc in self._escopo_ticker(ticker):
                if doc.chave in desejadas:
                    encontrados.append(doc)
        return encontrados

    def _tickers_em_cache(self: "CascataDocumentos") -> list[str]:
        """Lista os tickers com catálogo de documentos em cache."""
        base = self._catalog.base_dir
        tickers: set[str] = set()
        for raiz in ("bdr", "informe-mensal", "documentos-relevantes"):
            pasta = base / raiz
            if pasta.is_dir():
                tickers.update(item.name for item in pasta.iterdir() if item.is_dir())
        return sorted(tickers)

    def confirmar_leitura(
        self: "CascataDocumentos", documentos: list[DocumentoEscopo]
    ) -> bool:
        """Aplica o gate de confirmação antes de ler o texto integral."""
        if faixa_confirmacao(len(documentos)) == FAIXA_AUTOMATICA:
            return True
        if self._confirmar is None:
            return True
        nomes = [doc.nome for doc in documentos] if len(documentos) <= 7 else []
        return bool(self._confirmar(len(documentos), nomes))

    def preparar_texto(
        self: "CascataDocumentos", documentos: list[DocumentoEscopo]
    ) -> str:
        """Lê o texto integral dos alvos do cache, truncando o excedente.

        Documentos sem texto em cache são omitidos em silêncio: nenhum texto é
        extraído nem gravado sob demanda durante o chat.
        """
        textos = [
            texto
            for documento in documentos
            if (texto := self._text_store.obter(documento.ticker, documento.chave))
        ]
        return self._aplicar_orcamento(textos)

    def _aplicar_orcamento(self: "CascataDocumentos", textos: list[str]) -> str:
        """Aplica os tetos por documento e global, registrando o truncamento."""
        selecionados: list[str] = []
        total = 0
        truncado = False
        for texto in textos:
            if len(texto) > self._teto_documento:
                texto, truncado = texto[: self._teto_documento], True
            restante = self._teto_global - total
            if restante <= 0:
                truncado = True
                break
            if len(texto) > restante:
                texto, truncado = texto[:restante], True
            total += len(texto)
            selecionados.append(texto)
        if truncado:
            logger.warning(
                "Contexto do chat truncado pelo orçamento (teto global=%d).",
                self._teto_global,
            )
        return "\n\n".join(selecionados)

    @property
    def _text_store(self: "CascataDocumentos") -> DocumentTextStore:
        """Store de textos associado ao catálogo."""
        return self._catalog.text_store
