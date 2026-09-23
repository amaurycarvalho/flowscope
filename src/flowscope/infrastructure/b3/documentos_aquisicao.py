"""Aquisição sob demanda dos documentos de um ticker.

Escolhe a fonte pelo tipo do ativo: FIIs usam documentos relevantes e informe
mensal; ações e BDRs usam material facts (fatos relevantes e assembleias),
baixados do visualizador da CVM. Toda falha é tolerada, resultando em cache
vazio em vez de erro.
"""

import logging
from calendar import monthrange
from collections.abc import Callable
from datetime import date

from flowscope.application.cancellation import CancellationToken
from flowscope.domain.structured import (
    CategoriaMaterialFact,
    DocumentoMaterialFact,
)
from flowscope.infrastructure.b3.bdr.documents import id_protocolo
from flowscope.infrastructure.b3.documentos_relevantes import (
    DocumentosRelevantesProvider,
)
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.informe_mensal_cache import (
    InformeMensalArquivoProvider,
)
from flowscope.infrastructure.b3.reports_repository import _informes_aplicaveis
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm.pdf import baixar_pdf_cvm
from flowscope.infrastructure.fii.fundamentus.normalizers import para_data

logger = logging.getLogger("flowscope")

#: Janela de meses consultada para documentos relevantes, material facts e informe.
_MESES_DOCUMENTOS = 12

#: Tipo de relatório estruturado de informe mensal.
_TIPO_INFORME_MENSAL = 40

#: Categorias de material facts adquiridas e o slug de pasta correspondente.
_CATEGORIAS_MATERIAL_FACT: tuple[tuple[CategoriaMaterialFact, str], ...] = (
    (CategoriaMaterialFact.FATOS_RELEVANTES, "fato-relevante"),
    (CategoriaMaterialFact.ASSEMBLEIAS, "assembleia"),
)


class AquisicaoDocumentos:
    """Adquire e cacheia os documentos de um ticker conforme o tipo do ativo."""

    def __init__(
        self: "AquisicaoDocumentos",
        client: B3FundosClient | None = None,
        documentos: DocumentosRelevantesProvider | None = None,
        informes: InformeMensalArquivoProvider | None = None,
        cache: CacheManager | None = None,
        baixar_cvm: Callable[[str], bytes | None] | None = None,
    ) -> None:
        """Inicializa o orquestrador com cliente, provedores e download da CVM."""
        self._client = client or B3FundosClient(cache=cache)
        self._documentos = documentos or DocumentosRelevantesProvider(
            client=self._client, cache=cache
        )
        self._informes = informes or InformeMensalArquivoProvider(
            client=self._client, cache=cache
        )
        self._baixar_cvm = baixar_cvm or baixar_pdf_cvm

    def adquirir(
        self: "AquisicaoDocumentos",
        ticker: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> None:
        """Adquire os documentos do ticker conforme o tipo, tolerando falhas.

        ``progress``, quando informado, recebe ``(atual, total, rótulo)`` a
        cada documento processado. ``cancel_token``, quando informado, é
        observado no topo de cada unidade de trabalho, interrompendo a
        aquisição pela via de :class:`OperacaoCancelada`.
        """
        chave = (ticker or "").strip().upper()
        if not chave:
            return
        id_fnet = self._client.resolver_ticker(chave)
        if id_fnet:
            self._adquirir_fii(chave, id_fnet, reference_date, progress, cancel_token)
            return
        code_cvm = self._client.resolver_code_cvm(chave)
        if code_cvm:
            self._adquirir_acao(chave, code_cvm, reference_date, progress, cancel_token)

    def _adquirir_fii(
        self: "AquisicaoDocumentos",
        ticker: str,
        id_fnet: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> None:
        """Adquire documentos relevantes e o informe mensal de um FII."""
        inicio = _subtrair_meses(reference_date, _MESES_DOCUMENTOS)
        itens = self._listar_documentos_relevantes(
            ticker, id_fnet, inicio, reference_date
        )
        informe = self._selecionar_informe(ticker, id_fnet, reference_date)
        total = len(itens) + (1 if informe is not None else 0)
        self._reportar(progress, 0, total, ticker)
        atual = 0
        for item in itens:
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()
            self._persistir_documento_relevante(ticker, id_fnet, item)
            atual += 1
            self._reportar(progress, atual, total, ticker)
        if informe is not None:
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()
            self._persistir_informe(ticker, informe)
            atual += 1
            self._reportar(progress, atual, total, ticker)

    def _listar_documentos_relevantes(
        self: "AquisicaoDocumentos",
        ticker: str,
        id_fnet: str,
        inicio: date,
        reference_date: date,
    ) -> list[dict]:
        """Lista os documentos relevantes do FII, tolerando falha."""
        try:
            return self._client.listar_todos_documentos_relevantes(
                id_fnet, inicio, reference_date
            )
        except Exception:  # falha de listagem isolada por fonte
            logger.warning(
                "Falha ao listar documentos relevantes de %s",
                ticker,
                exc_info=True,
            )
            return []

    def _persistir_documento_relevante(
        self: "AquisicaoDocumentos",
        ticker: str,
        id_fnet: str,
        item: dict,
    ) -> None:
        """Baixa e grava um documento relevante, tolerando falha."""
        try:
            self._documentos.persistir(ticker, id_fnet, item)
        except Exception:  # falha isolada por documento
            logger.warning(
                "Falha ao adquirir documento relevante de %s",
                ticker,
                exc_info=True,
            )

    def _selecionar_informe(
        self: "AquisicaoDocumentos",
        ticker: str,
        id_fnet: str,
        reference_date: date,
    ) -> dict | None:
        """Seleciona o informe mensal mais recente aplicável do FII."""
        inicio = _subtrair_meses(reference_date, _MESES_DOCUMENTOS)
        try:
            documentos = self._client.listar_documentos(
                id_fnet,
                inicio,
                reference_date,
                _TIPO_INFORME_MENSAL,
                tolerante=False,
            )
        except Exception:  # indisponibilidade distinta de ausência
            logger.warning(
                "Falha ao listar informes mensais de %s", ticker, exc_info=True
            )
            return None
        candidatos = _informes_aplicaveis(documentos, reference_date)
        if not candidatos:
            return None
        return max(candidatos, key=lambda item: item[0])[1]

    def _persistir_informe(
        self: "AquisicaoDocumentos", ticker: str, documento: dict
    ) -> None:
        """Grava o informe mensal selecionado, tolerando falha."""
        try:
            self._informes.persistir(ticker, documento)
        except Exception:  # falha isolada de gravação
            logger.warning(
                "Falha ao persistir informe mensal de %s",
                ticker,
                exc_info=True,
            )

    def _adquirir_acao(
        self: "AquisicaoDocumentos",
        ticker: str,
        code_cvm: str,
        reference_date: date,
        progress: Callable[[int, int, str], None] | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> None:
        """Adquire os material facts de uma ação ou BDR."""
        inicio = _subtrair_meses(reference_date, _MESES_DOCUMENTOS)
        documentos: list[tuple[DocumentoMaterialFact, str]] = []
        for categoria, slug in _CATEGORIAS_MATERIAL_FACT:
            for documento in self._listar_material_facts(
                ticker, code_cvm, categoria, inicio, reference_date
            ):
                documentos.append((documento, slug))
        total = len(documentos)
        self._reportar(progress, 0, total, ticker)
        for atual, (documento, slug) in enumerate(documentos, start=1):
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()
            self._persistir_material_fact(
                ticker, documento, slug, reference_date
            )
            self._reportar(progress, atual, total, ticker)

    @staticmethod
    def _reportar(
        progress: Callable[[int, int, str], None] | None,
        current: int,
        total: int,
        ticker: str,
    ) -> None:
        """Notifica o progresso da aquisição, quando há callback."""
        if progress is None:
            return
        if total > 0:
            label = f"• Documentos de {ticker} ({current}/{total})"
        else:
            label = f"• Documentos de {ticker}..."
        progress(current, total, label)

    def _listar_material_facts(
        self: "AquisicaoDocumentos",
        ticker: str,
        code_cvm: str,
        categoria: CategoriaMaterialFact,
        inicio: date,
        reference_date: date,
    ) -> list[DocumentoMaterialFact]:
        """Lista os material facts de uma categoria, tolerando falha."""
        try:
            return self._client.listar_fatos_relevantes(
                code_cvm, categoria, inicio, reference_date, ticker=ticker
            )
        except Exception:  # falha de listagem isolada por categoria
            logger.warning(
                "Falha ao listar material facts de %s", ticker, exc_info=True
            )
            return []

    def _persistir_material_fact(
        self: "AquisicaoDocumentos",
        ticker: str,
        documento: DocumentoMaterialFact,
        slug: str,
        reference_date: date,
    ) -> None:
        """Baixa e grava o PDF de um material fact, tolerando falhas."""
        protocolo = id_protocolo(documento.url_documento or "")
        if protocolo is None:
            return
        referencia = _data_documento(documento.data_referencia, reference_date)
        cache = self._documentos.cache
        if cache.existe(ticker, referencia, slug, protocolo):
            return
        try:
            conteudo = self._baixar_cvm(protocolo)
        except Exception:  # falha de rede isolada por documento
            logger.warning(
                "Falha ao baixar material fact %s de %s",
                protocolo,
                ticker,
                exc_info=True,
            )
            return
        if not conteudo:
            return
        cache.gravar(ticker, referencia, slug, protocolo, conteudo)


def _data_documento(texto: object, fallback: date) -> date:
    """Interpreta a data de referência do documento, ou usa o fallback."""
    if texto:
        iso = _data_iso(texto)
        if iso is not None:
            return iso
        convertida = para_data(str(texto))
        if convertida is not None:
            return convertida
    return fallback


def _data_iso(valor: object) -> date | None:
    """Interpreta uma data ISO (com ou sem horário) como ``date``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _subtrair_meses(data: date, meses: int) -> date:
    """Subtrai um número de meses de uma data, ajustando o dia ao mês."""
    total = data.year * 12 + (data.month - 1) - meses
    ano, mes = divmod(total, 12)
    dia = min(data.day, monthrange(ano, mes + 1)[1])
    return date(ano, mes + 1, dia)
