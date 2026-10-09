"""Ramo ``/guidance`` da árvore de conhecimento sobre o ledger em cache.

O ramo é estritamente somente-leitura: lê as entradas do ledger de guidance já
avaliadas, agrupa-as por ticker, ano e mês da data do relatório e expõe uma
folha por entrada com o texto formatado e o rótulo curado do Relatório
Gerencial associado. Nenhuma avaliação, gravação ou reextração é feita durante
o chat, e os tickers sem entrada com valor são omitidos.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from flowscope.application.chat.arvore import No, no_folha, no_interno
from flowscope.application.documentos.document_guidance import (
    EntradaGuidanceArvore,
    agrupar_entradas,
    chave_curta_guidance,
    conteudo_arvore_guidance,
    rotulo_relatorio_gerencial,
)
from flowscope.application.fundamental.linhas import mes_ano
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo

logger = logging.getLogger("flowscope")

#: Teto de caracteres do índice compacto de guidance por ticker.
TETO_INDICE = 6000


def _achatar(catalogo: CatalogoTicker) -> list[DocumentoArquivo]:
    """Percorre a hierarquia do catálogo devolvendo os arquivos em ordem."""
    return [
        arquivo
        for ano in catalogo.anos
        for mes in ano.meses
        for categoria in mes.categorias
        for arquivo in categoria.arquivos
    ]


class FonteGuidance:
    """Provedor do ramo ``/guidance`` a partir do ledger em cache."""

    def __init__(
        self: FonteGuidance,
        tickers: Iterable[str] = (),
        service: object | None = None,
        catalogo: object | None = None,
    ) -> None:
        """Guarda os tickers, o serviço de guidance e o catálogo de documentos."""
        self._tickers = list(tickers)
        self._service = service
        self._catalogo = catalogo

    def construir(self: FonteGuidance) -> No | None:
        """Constrói o ramo ``/guidance``, ou ``None`` sem nenhuma entrada."""
        raiz = no_interno("/guidance", "guidance")
        algum = False
        for ticker in self._tickers:
            no_ticker = self._construir_ticker(ticker)
            if no_ticker is None:
                continue
            raiz.filho(no_ticker)
            algum = True
        return raiz if algum else None

    def _construir_ticker(self: FonteGuidance, ticker: str) -> No | None:
        """Constrói o nó ``/guidance/<ticker>`` com anos, meses e folhas."""
        entradas = self._entradas(ticker)
        if not entradas:
            return None
        documentos = self._documentos(ticker)
        no_ticker = no_interno(f"/guidance/{ticker}", ticker)
        base = f"/guidance/{ticker}"
        indice = self._indice(entradas, documentos)
        no_ticker.filho(
            no_folha(
                f"{base}/indice",
                "indice",
                conteudo=indice,
                campos={"indice": indice},
            )
        )
        for ano, meses in agrupar_entradas(entradas):
            no_ano = no_interno(f"{base}/{ano}", str(ano))
            no_ticker.filho(no_ano)
            for mes, itens in meses:
                no_mes = no_interno(f"{base}/{ano}/{mes:02d}", f"{mes:02d}")
                no_ano.filho(no_mes)
                for entrada in itens:
                    no_mes.filho(self._folha(base, ano, mes, entrada, documentos))
        return no_ticker

    @staticmethod
    def _folha(
        base: str,
        ano: int,
        mes: int,
        entrada: EntradaGuidanceArvore,
        documentos: dict[Path, DocumentoArquivo],
    ) -> No:
        """Monta a folha de uma entrada com o texto e o rótulo do RG.

        O rótulo curado do RG fica no ``metadado`` (visível em ``listar``) e em
        ``campos`` (pesquisável), para a LLM associar o guidance ao relatório
        mesmo sem abrir a folha.
        """
        rotulo = rotulo_relatorio_gerencial(
            entrada.data_relatorio, entrada.caminho_pdf, documentos
        )
        return no_folha(
            f"{base}/{ano}/{mes:02d}/{chave_curta_guidance(entrada.chave)}",
            entrada.texto,
            conteudo=conteudo_arvore_guidance(entrada, documentos),
            metadado=rotulo,
            campos={
                "guidance": entrada.texto,
                "relatorio": rotulo,
                "periodo": f"{ano:04d}/{mes:02d}",
            },
        )

    @staticmethod
    def _indice(
        entradas: list[EntradaGuidanceArvore],
        documentos: dict[Path, DocumentoArquivo],
    ) -> str:
        """Monta o índice cronológico decrescente das entradas de guidance."""
        ordenadas = sorted(
            entradas, key=lambda e: (e.ano, e.mes), reverse=True
        )
        linhas = [
            f"{mes_ano(entrada.data_relatorio)}: {entrada.texto} — "
            f"{rotulo_relatorio_gerencial(entrada.data_relatorio, entrada.caminho_pdf, documentos)}"
            for entrada in ordenadas
        ]
        return "\n".join(linhas)[:TETO_INDICE]

    def _entradas(
        self: FonteGuidance, ticker: str
    ) -> list[EntradaGuidanceArvore]:
        """Lê as entradas do ledger do ticker, tolerando falha de leitura."""
        metodo = getattr(self._service, "entradas_arvore", None)
        if not callable(metodo):
            return []
        try:
            return list(metodo(ticker))
        except Exception:
            logger.warning("Falha ao ler o guidance de %s", ticker, exc_info=True)
            return []

    def _documentos(
        self: FonteGuidance, ticker: str
    ) -> dict[Path, DocumentoArquivo]:
        """Mapeia caminho → documento do catálogo do ticker, se disponível."""
        metodo = getattr(self._catalogo, "catalogo", None)
        if not callable(metodo):
            return {}
        try:
            return {arquivo.caminho: arquivo for arquivo in _achatar(metodo(ticker))}
        except Exception:
            logger.warning(
                "Falha ao ler o catálogo de %s para o guidance",
                ticker,
                exc_info=True,
            )
            return {}
