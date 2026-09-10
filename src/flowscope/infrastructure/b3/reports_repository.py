"""Repositório de relatórios estruturados da B3 (RFC-008 §10-16).

Lista os documentos de rendimentos/amortizações (type 41), extrai os proventos
via ``structured_extractor`` e produz um resultado de aquisição que preserva os
dados brutos e metadados, distinguindo lista vazia de falha.
"""

import logging
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

from flowscope.domain.b3 import (
    AcquisitionMetadata,
    AcquisitionResult,
    B3InformeMensal,
    B3ReportReference,
)
from flowscope.domain.structured import DocumentoProvento
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.informe_mensal_parser import (
    extrair_informe_mensal,
)
from flowscope.infrastructure.b3.structured_repository import FundosRepository

logger = logging.getLogger("flowscope")

#: Tipo de relatório estruturado de rendimentos e amortizações.
TIPO_RENDIMENTOS = 41

#: Tipo de relatório estruturado de informe mensal.
TIPO_INFORME_MENSAL = 40

#: Fonte registrada nos metadados de aquisição.
FONTE_B3 = "B3"

#: Versão do parser/aquisição.
PARSER_VERSION = "b3-fii-1"


class B3ReportsRepository:
    """Lista e extrai relatórios estruturados de um fundo da B3."""

    def __init__(
        self: "B3ReportsRepository", client: B3FundosClient | None = None
    ) -> None:
        """Inicializa o repositório com o cliente e o extrator de documentos."""
        self._client = client or B3FundosClient()
        self._fundos = FundosRepository(self._client)

    def get_distributions(
        self: "B3ReportsRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
    ) -> list[B3ReportReference]:
        """Lista as referências de rendimentos/amortizações do período."""
        documentos = self._client.listar_documentos(
            id_fnet, data_inicio, data_fim, TIPO_RENDIMENTOS
        )
        return _referencias(documentos)

    def get_monthly_reports(
        self: "B3ReportsRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
    ) -> list[B3ReportReference]:
        """Lista as referências de informes mensais do período."""
        documentos = self._client.listar_documentos(
            id_fnet, data_inicio, data_fim, TIPO_INFORME_MENSAL
        )
        return _referencias(documentos)

    def extrair_informe(
        self: "B3ReportsRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        reference_date: date,
    ) -> B3InformeMensal | None:
        """Extrai o informe mensal ativo mais recente até a data de referência.

        Retorna ``None`` quando não há informe aplicável (ausência de dados).
        Uma falha de listagem ou download propaga a exceção, distinguindo-a de
        ausência.
        """
        documentos = self._client.listar_documentos(
            id_fnet, data_inicio, data_fim, TIPO_INFORME_MENSAL, tolerante=False
        )
        candidatos = _informes_aplicaveis(documentos, reference_date)
        if not candidatos:
            return None
        referencia, documento = max(
            candidatos, key=lambda item: item[0]
        )
        url = str(documento.get("urlViewerFundosNet") or "")
        id_documento = _id_da_url(url)
        if id_documento is None:
            raise ValueError(f"Informe sem identificador de documento: {url!r}")
        html = self._client.buscar_html_documento(str(id_documento))
        return extrair_informe_mensal(
            html,
            document_id=id_documento,
            reference_date=referencia,
            reference_month=documento.get("referenceDateFormat"),
        )

    def acquire_distributions(
        self: "B3ReportsRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
    ) -> AcquisitionResult:
        """Adquire rendimentos preservando bruto/metadados e sinalizando falha."""
        payload = _payload(id_fnet, data_inicio, data_fim)
        metadata = AcquisitionMetadata(
            source=FONTE_B3,
            endpoint="GetStructuredReports(type=41)",
            request_payload=payload,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            parser_version=PARSER_VERSION,
        )
        try:
            documentos = self._client.listar_documentos(
                id_fnet,
                data_inicio,
                data_fim,
                TIPO_RENDIMENTOS,
                tolerante=False,
            )
        except Exception as exc:  # falha de aquisição distinta de lista vazia
            logger.warning(
                "Falha ao adquirir rendimentos de %s", id_fnet, exc_info=True
            )
            return AcquisitionResult(
                errors=(f"distributions unavailable: {exc}",),
                metadata=(metadata,),
            )
        return AcquisitionResult(
            distributions=tuple(_referencias(documentos)),
            raw_documents=tuple(documentos),
            metadata=(metadata,),
        )

    def extrair_proventos(
        self: "B3ReportsRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        ticker: str,
    ) -> list[DocumentoProvento]:
        """Extrai os proventos dos documentos listados, tolerando falhas."""
        documentos = self._client.listar_documentos(
            id_fnet, data_inicio, data_fim, TIPO_RENDIMENTOS
        )
        proventos: list[DocumentoProvento] = []
        for documento in documentos:
            contexto = dict(documento)
            contexto.setdefault("ticker", ticker)
            contexto.setdefault("id_fnet", id_fnet)
            try:
                proventos.append(self._fundos.extrair_detalhes(contexto))
            except Exception:  # documento sem provento extraível
                logger.warning(
                    "Falha ao extrair documento de %s", ticker, exc_info=True
                )
        return proventos


def _payload(id_fnet: str, data_inicio: date, data_fim: date) -> dict:
    """Monta o payload de consulta de relatórios estruturados."""
    return {
        "language": "pt-br",
        "dataInicial": data_inicio.isoformat(),
        "dataFinal": data_fim.isoformat(),
        "idFNET": id_fnet,
        "typeFund": "FII",
        "type": TIPO_RENDIMENTOS,
    }


def _referencias(documentos: list[dict]) -> list[B3ReportReference]:
    """Retorna as referências normalizadas, ignorando documentos sem id."""
    referencias: list[B3ReportReference] = []
    for documento in documentos:
        referencia = _para_referencia(documento)
        if referencia is not None:
            referencias.append(referencia)
    return referencias


def _para_referencia(documento: dict) -> B3ReportReference | None:
    """Monta uma referência normalizada a partir de um documento bruto."""
    url = str(documento.get("urlViewerFundosNet") or "")
    id_documento = _id_da_url(url)
    if id_documento is None:
        return None
    return B3ReportReference(
        document_id=id_documento,
        reference_date=_data_iso(documento.get("referenceDate")),
        delivery_date=documento.get("deliveryDateFormat"),
        report_type=str(documento.get("describleType") or ""),
        status=str(documento.get("status") or ""),
        viewer_url=url,
        version=int(documento.get("version") or 1),
    )


def _id_da_url(url: str) -> int | None:
    """Extrai o identificador numérico do documento a partir da URL."""
    consulta = parse_qs(urlparse(url).query)
    valores = consulta.get("id")
    if not valores:
        return None
    try:
        return int(valores[0])
    except ValueError:
        return None


def _data_iso(valor: object) -> date | None:
    """Interpreta uma data ISO (com ou sem horário) como ``date``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _informes_aplicaveis(
    documentos: list[dict], reference_date: date
) -> list[tuple[date, dict]]:
    """Filtra informes ativos com referência não posterior à data informada."""
    candidatos: list[tuple[date, dict]] = []
    for documento in documentos:
        if not _is_active(str(documento.get("status") or "")):
            continue
        referencia = _data_iso(documento.get("referenceDate"))
        if referencia is None or referencia > reference_date:
            continue
        candidatos.append((referencia, documento))
    return candidatos


def _is_active(status: str) -> bool:
    """Indica se o documento está ativo."""
    return status.startswith("1 (Ativo)")
