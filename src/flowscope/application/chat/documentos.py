"""Ramo ``/documentos`` da árvore de conhecimento sobre o cache local.

O ramo é estritamente somente-leitura de cache: lê os resumos curtos e longos do
catálogo de documentos e o texto integral já extraído e em cache. Documentos
pendentes de resumo ou de extração são omitidos em silêncio — nenhum resumo é
gerado e nenhum texto é extraído durante o chat.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.catalogo import (
    CatalogoDocumentos,
    chave_documento,
)
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo

logger = logging.getLogger("flowscope")

#: Teto de caracteres por nó de documento enviado à LLM.
TETO_DOCUMENTO = 12000

#: Raízes de cache onde vivem os catálogos por ticker.
_RAIZES = ("bdr", "informe-mensal", "documentos-relevantes")


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


class FonteDocumentos:
    """Provedor do ramo ``/documentos`` a partir do catálogo em cache."""

    def __init__(
        self: FonteDocumentos,
        catalog: CatalogoDocumentos | None = None,
        teto_texto: int = TETO_DOCUMENTO,
    ) -> None:
        """Guarda o catálogo e o teto de texto por nó."""
        self._catalog = catalog
        self._teto_texto = teto_texto

    def construir(self: FonteDocumentos) -> No:
        """Constrói o ramo ``/documentos`` com os documentos recuperáveis."""
        raiz = no_interno("/documentos", "documentos")
        tickers_no = no_interno("/documentos/tickers", "tickers")
        raiz.filho(tickers_no)
        for ticker in self._tickers_em_cache():
            no_ticker = self._construir_ticker(ticker)
            if no_ticker.folha:
                continue
            raiz.filho(no_ticker)
            tickers_no.filho(
                no_folha(
                    f"/documentos/tickers/{ticker}",
                    ticker,
                    conteudo=ticker,
                    campos={"ticker": ticker},
                )
            )
        return raiz

    def _construir_ticker(self: FonteDocumentos, ticker: str) -> No:
        """Constrói o nó ``/documentos/<ticker>`` com curto/longo/texto.

        Só entram os nós com conteúdo; o texto integral é lido do cache apenas
        quando a LLM pede o nó (``carregar``), para não reler o conteúdo a cada
        envio.
        """
        escopos = self._escopo_ticker(ticker)
        no_ticker = no_interno(f"/documentos/{ticker}", ticker)
        base = f"/documentos/{ticker}"
        self._anexar_folha(
            no_ticker,
            base,
            "curto",
            self._juntar(e.short_summary for e in escopos),
            "resumo",
        )
        self._anexar_folha(
            no_ticker,
            base,
            "longo",
            self._juntar(e.long_summary for e in escopos),
            "resumo",
        )
        if escopos and self._tem_texto(ticker):
            no_ticker.filho(
                no_folha(
                    f"{base}/texto",
                    "texto",
                    carregar=lambda t=ticker, e=escopos: self._texto_integral(t, e),
                    campo_pesado="texto",
                )
            )
        return no_ticker

    @staticmethod
    def _anexar_folha(
        pai: No, base: str, segmento: str, conteudo: str, campo: str
    ) -> None:
        """Anexa ao nó do ticker uma folha quando há conteúdo."""
        if conteudo:
            pai.filho(
                no_folha(
                    f"{base}/{segmento}",
                    segmento,
                    conteudo=conteudo,
                    campos={campo: conteudo},
                )
            )

    def _escopo_ticker(self: FonteDocumentos, ticker: str) -> list[DocumentoEscopo]:
        """Monta os documentos do escopo a partir do catálogo de um ticker."""
        if self._catalog is None:
            return []
        return [
            DocumentoEscopo(
                ticker=arquivo.ticker,
                nome=arquivo.nome,
                categoria=arquivo.categoria,
                ano=arquivo.ano,
                mes=arquivo.mes,
                chave=chave_documento(arquivo.caminho, self._catalog.base_dir),
                caminho=arquivo.caminho,
                short_summary=arquivo.short_summary,
                long_summary=arquivo.long_summary,
            )
            for arquivo in _achatar(self._catalog.catalogo(ticker))
        ]

    def _tem_texto(self: FonteDocumentos, ticker: str) -> bool:
        """Indica se há texto em cache para o ticker, lendo o mapa uma vez."""
        store = self._text_store
        mapa = self._mapa_textos(store, ticker)
        return any(mapa.values())

    def _texto_integral(
        self: FonteDocumentos, ticker: str, escopos: list[DocumentoEscopo]
    ) -> str:
        """Lê o texto em cache dos documentos do ticker, truncando o excedente."""
        store = self._text_store
        if store is None:
            return ""
        mapa = self._mapa_textos(store, ticker)
        textos = []
        total = 0
        for escopo in escopos:
            texto = mapa.get(escopo.chave) or ""
            if not texto:
                continue
            restante = self._teto_texto - total
            if restante <= 0:
                break
            textos.append(texto[:restante])
            total += len(textos[-1])
        return "\n\n".join(textos)

    @staticmethod
    def _mapa_textos(store: DocumentTextStore | None, ticker: str) -> dict[str, str]:
        """Obtém o mapa de textos do ticker lendo o cache no máximo uma vez."""
        if store is None:
            return {}
        obter_mapa = getattr(store, "textos", None)
        if callable(obter_mapa):
            try:
                return dict(obter_mapa(ticker))
            except Exception:
                logger.warning("Falha ao ler os textos de %s", ticker, exc_info=True)
                return {}
        return {}

    @staticmethod
    def _juntar(parciais: Iterable[str | None]) -> str:
        """Junta resumos não vazios, em ordem."""
        return "\n\n".join(p for p in parciais if p)

    def _tickers_em_cache(self: FonteDocumentos) -> list[str]:
        """Lista os tickers com catálogo de documentos em cache."""
        if self._catalog is None:
            return []
        base = self._catalog.base_dir
        tickers: set[str] = set()
        for raiz in _RAIZES:
            pasta = base / raiz
            if pasta.is_dir():
                tickers.update(item.name for item in pasta.iterdir() if item.is_dir())
        return sorted(tickers)

    @property
    def _text_store(self: FonteDocumentos) -> DocumentTextStore | None:
        """Store de textos associado ao catálogo."""
        return self._catalog.text_store if self._catalog is not None else None
