"""Provider de dividendos de BDR como fonte secundária.

Implementa a porta ``DividendHistoryProvider`` e a extensão ``obter_dados_bdr``
que também devolve o caminho do cache de PDFs e a identidade fiscal
(depositário, empresa e ISIN) extraída dos avisos aos acionistas.
"""

import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

from flowscope.domain.bdr import AvisoBdr, DadosBdr, DividendoBdr
from flowscope.domain.fii.dividends import (
    DividendoConsolidado,
    consolidar_dividendos,
)
from flowscope.infrastructure.b3.bdr.cache import PdfCache
from flowscope.infrastructure.b3.bdr.client import BdrClient
from flowscope.infrastructure.b3.bdr.constants import MESES_JANELA, PASTA_CACHE
from flowscope.infrastructure.b3.bdr.news import listar_avisos
from flowscope.infrastructure.b3.bdr.parser import parse_dividendo
from flowscope.infrastructure.b3.bdr.text import extrair_texto
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.fundamentus.normalizers import para_data

logger = logging.getLogger("flowscope")

#: Assinatura do extrator de texto de PDF.
ExtratorTexto = Callable[[bytes], str]


class BdrDividendProvider:
    """Fornece dividendos e identidade fiscal de BDRs a partir do Plantão B3."""

    def __init__(
        self: "BdrDividendProvider",
        client: BdrClient | None = None,
        cache_dir: Path | None = None,
        cache: CacheManager | None = None,
        extractor: ExtratorTexto | None = None,
        meses: int = MESES_JANELA,
    ) -> None:
        """Inicializa o provider com o cliente, o cache e o extrator de texto."""
        self._client = client or BdrClient()
        base = (
            Path(cache_dir)
            if cache_dir is not None
            else (cache or CacheManager()).get_cache_dir() / PASTA_CACHE
        )
        self._pdf_cache = PdfCache(base)
        self._cache = cache
        self._extractor = extractor or extrair_texto
        self._meses = meses

    def obter_dividendos(
        self: "BdrDividendProvider",
        ticker: str,
        reference_date: date,
    ) -> list[DividendoConsolidado]:
        """Retorna os dividendos extraídos dos avisos do BDR."""
        dados = self.obter_dados_bdr(ticker, reference_date)
        return list(dados.dividendos) if dados is not None else []

    def obter_dados_bdr(
        self: "BdrDividendProvider",
        ticker: str,
        reference_date: date,
    ) -> DadosBdr | None:
        """Extrai dividendos e identidade fiscal dos avisos do BDR.

        Falhas de listagem ou de um aviso isolado são toleradas; o resultado
        pode ser vazio, mas nunca lança exceção para não interromper a análise
        do ticker.
        """
        try:
            avisos = listar_avisos(
                self._client.coletar_noticias,
                ticker,
                reference_date,
                cache=self._cache,
                meses=self._meses,
            )
        except Exception:  # falha de aquisição isolada por ticker
            logger.warning(
                "Falha ao listar avisos de BDR de %s", ticker, exc_info=True
            )
            return None
        return self._consolidar_avisos(ticker, avisos, reference_date)

    def _consolidar_avisos(
        self: "BdrDividendProvider",
        ticker: str,
        avisos: list[AvisoBdr],
        reference_date: date,
    ) -> DadosBdr:
        """Consolida os avisos em dividendos e identidade fiscal do BDR."""
        dividendos: list[DividendoConsolidado] = []
        depositario: str | None = None
        empresa: str | None = None
        isin: str | None = None
        nivel: str | None = None
        observacao: str | None = None
        for aviso in avisos:
            dividendo = self._extrair_dividendo(ticker, aviso, reference_date)
            if dividendo is None:
                continue
            depositario = depositario or dividendo.depositario
            empresa = empresa or dividendo.empresa
            isin = isin or dividendo.isin
            nivel = nivel or dividendo.nivel_programa
            observacao = observacao or dividendo.observacao
            consolidado = dividendo.para_consolidado()
            if consolidado is not None:
                dividendos.append(consolidado)

        return DadosBdr(
            dividendos=tuple(consolidar_dividendos(dividendos)),
            nome_depositario=depositario,
            nome_empresa=empresa,
            isin=isin,
            nivel_programa=nivel,
            observacao=observacao,
            avisos=tuple(aviso.titulo for aviso in avisos),
        )

    def _extrair_dividendo(
        self: "BdrDividendProvider",
        ticker: str,
        aviso: AvisoBdr,
        reference_date: date,
    ) -> DividendoBdr | None:
        """Baixa (ou lê do cache) o PDF do aviso e extrai o dividendo."""
        dados_pdf = self._obter_pdf(ticker, aviso, reference_date)
        if dados_pdf is None:
            return None
        texto = self._extractor(dados_pdf)
        return parse_dividendo(texto)

    def _obter_pdf(
        self: "BdrDividendProvider",
        ticker: str,
        aviso: AvisoBdr,
        reference_date: date,
    ) -> bytes | None:
        """Obtém o PDF do aviso, reutilizando o cache e tolerando falha de rede."""
        referencia = _data_aviso(aviso, reference_date)
        if self._pdf_cache.existe(ticker, referencia, aviso.id_noticia):
            return self._pdf_cache.ler(ticker, referencia, aviso.id_noticia)
        try:
            dados = self._client.obter_pdf_de_aviso(
                aviso.id_noticia, referencia
            )
        except Exception:  # falha de rede isolada por aviso
            logger.warning(
                "Falha ao baixar PDF do aviso %s", aviso.id_noticia, exc_info=True
            )
            dados = None
        if dados is None:
            return self._pdf_cache.ler(ticker, referencia, aviso.id_noticia)
        self._pdf_cache.gravar(ticker, referencia, aviso.id_noticia, dados)
        return dados


def _data_aviso(aviso: AvisoBdr, reference_date: date) -> date:
    """Resolve a data de referência do aviso para a árvore de cache."""
    texto = (aviso.data_publicacao or "").strip()
    if texto:
        try:
            return date.fromisoformat(texto[:10])
        except ValueError:
            convertida = para_data(texto)
            if convertida is not None:
                return convertida
    return reference_date
