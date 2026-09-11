"""Modelos normalizados da aquisição B3 (RFC-008 §21/§27/§39)."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class B3Fund:
    """Identidade normalizada de um fundo na B3."""

    ticker: str
    fnet_id: str
    primary_id: str | None
    name: str
    trading_name: str | None


@dataclass(frozen=True)
class B3ReportReference:
    """Referência a um documento estruturado listado na B3."""

    document_id: int
    reference_date: date | None
    delivery_date: str | None
    report_type: str
    status: str
    viewer_url: str
    version: int = 1


@dataclass(frozen=True)
class B3InformeMensal:
    """Informe Mensal Estruturado extraído de um documento FundosNet.

    Reúne os campos de cotistas, patrimônio líquido, cotas emitidas e valor
    patrimonial por cota reportados pelo fundo no mês de referência.
    """

    document_id: int
    reference_date: date | None
    reference_month: str | None
    cotistas: int | None
    patrimonio_liquido: Decimal | None
    cotas_emitidas: Decimal | None
    valor_patrimonial_cota: Decimal | None
    cnpj: str | None = None
    nome_administrador: str | None = None
    cnpj_administrador: str | None = None
    classificacao: str | None = None
    subclassificacao: str | None = None
    gestao: str | None = None
    segmento_atuacao: str | None = None
    fonte: str = "B3"


@dataclass(frozen=True)
class AcquisitionMetadata:
    """Metadados de uma operação de aquisição (RFC-008 §27)."""

    source: str
    endpoint: str
    request_payload: dict = field(default_factory=dict)
    retrieved_at: str = ""
    http_status: int = 200
    parser_version: str = ""


@dataclass(frozen=True)
class AcquisitionResult:
    """Resultado de aquisição que distingue lista vazia de falha (RFC-008 §39)."""

    fund: B3Fund | None = None
    distributions: tuple[B3ReportReference, ...] = ()
    raw_documents: tuple[dict, ...] = ()
    metadata: tuple[AcquisitionMetadata, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def disponivel(self: "AcquisitionResult") -> bool:
        """Indica se a aquisição concluiu sem erros registrados."""
        return not self.errors
