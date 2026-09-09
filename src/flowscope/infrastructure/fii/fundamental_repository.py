"""Adaptador do repositório fundamentalista sobre fontes B3/CVM existentes.

Consome ``Provento``/``Entidade`` do ``structured-earnings`` (via
``ExtrairProventosUseCase``) e a identidade ``code-cvm-resolution`` do
``regulacao-mercado``. A resolução é tolerante: sem dados, devolve listas
vazias ou ``None`` sem propagar exceção.
"""

import logging
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import Protocol

from flowscope.application.structured_use_cases import ExtrairProventosUseCase
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.domain.structured import DocumentoProvento, Provento
from flowscope.infrastructure.b3.structured_repository import FundosRepository

logger = logging.getLogger("flowscope")

_MESES_JANELA = 24


class FontePatrimonio(Protocol):
    """Fonte de patrimônio líquido, cotas e cotistas de um FII."""

    def patrimonio(
        self: "FontePatrimonio", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Retorna o patrimônio do ticker, ou ``None`` quando indisponível."""
        ...


def _subtrair_meses(data: date, meses: int) -> date:
    """Subtrai um número de meses de uma data, ajustando o dia ao mês."""
    total = data.year * 12 + (data.month - 1) - meses
    ano, mes = divmod(total, 12)
    dia = min(data.day, monthrange(ano, mes + 1)[1])
    return date(ano, mes + 1, dia)


class FundamentalRepository:
    """Implementa ``FiiFundamentalRepository`` com dados da B3/FNet e CVM."""

    def __init__(
        self: "FundamentalRepository",
        proventos_use_case: ExtrairProventosUseCase | None = None,
        patrimonio_source: FontePatrimonio | None = None,
    ) -> None:
        """Inicializa o repositório com o caso de uso de proventos e a CVM."""
        self._proventos = proventos_use_case or ExtrairProventosUseCase(
            FundosRepository()
        )
        self._patrimonio_source = patrimonio_source
        self._documentos_cache: dict[tuple[str, date], list[DocumentoProvento]] = {}

    def _buscar_documentos(
        self: "FundamentalRepository", ticker: str, reference_date: date
    ) -> list[DocumentoProvento]:
        """Busca e memoriza os documentos de proventos do ticker."""
        chave = (ticker, reference_date)
        if chave in self._documentos_cache:
            return self._documentos_cache[chave]
        try:
            inicio = _subtrair_meses(reference_date, _MESES_JANELA)
            documentos = self._proventos.execute(
                ticker, data_inicio=inicio, data_fim=reference_date
            )
        except Exception:  # resolução tolerante
            logger.warning(
                "Falha ao obter proventos de %s em %s",
                ticker,
                reference_date,
                exc_info=True,
            )
            documentos = []
        self._documentos_cache[chave] = documentos
        return documentos

    def obter_nome(self: "FundamentalRepository", ticker: str) -> str | None:
        """Retorna o nome do fundo a partir do primeiro documento disponível."""
        hoje = datetime.now(timezone.utc).date()
        documentos = self._buscar_documentos(ticker, hoje)
        if not documentos:
            return None
        return documentos[0].entidade.nome

    def obter_proventos(
        self: "FundamentalRepository", ticker: str, reference_date: date
    ) -> list[Provento]:
        """Retorna os proventos do ticker disponíveis até a data de referência."""
        documentos = self._buscar_documentos(ticker, reference_date)
        return [documento.provento for documento in documentos]

    def obter_patrimonio(
        self: "FundamentalRepository", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Retorna patrimônio e cotas do ticker via fonte CVM, ou ``None``."""
        if self._patrimonio_source is None:
            return None
        return self._patrimonio_source.patrimonio(ticker, reference_date)
