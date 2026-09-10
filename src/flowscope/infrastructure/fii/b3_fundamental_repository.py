"""Repositório fundamentalista apoiado na camada B3 (RFC-008).

Fornece nome e proventos a partir da identidade e dos documentos da B3. O
patrimônio permanece indisponível nesta fase (fonte CVM na change seguinte).
"""

import logging
from calendar import monthrange
from datetime import date

from flowscope.domain.b3 import B3Fund
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.domain.structured import Provento
from flowscope.infrastructure.b3.fund_repository import B3FundRepository
from flowscope.infrastructure.b3.reports_repository import B3ReportsRepository

logger = logging.getLogger("flowscope")

_MESES_JANELA = 24


class B3FundamentalRepository:
    """Implementa ``FiiFundamentalRepository`` com dados da B3."""

    def __init__(
        self: "B3FundamentalRepository",
        fund_repository: B3FundRepository | None = None,
        reports_repository: B3ReportsRepository | None = None,
    ) -> None:
        """Inicializa o repositório com os repositórios B3 de fundo e relatórios."""
        self._fundos = fund_repository or B3FundRepository()
        self._relatorios = reports_repository or B3ReportsRepository()
        self._fundos_cache: dict[str, B3Fund | None] = {}

    def obter_nome(self: "B3FundamentalRepository", ticker: str) -> str | None:
        """Retorna o nome do fundo a partir da identidade B3."""
        fundo = self._resolver(ticker)
        if fundo is None:
            return None
        return str(fundo.name) or None

    def obter_proventos(
        self: "B3FundamentalRepository", ticker: str, reference_date: date
    ) -> list[Provento]:
        """Retorna os proventos do ticker disponíveis até a data de referência."""
        fundo = self._resolver(ticker)
        if fundo is None:
            return []
        inicio = _subtrair_meses(reference_date, _MESES_JANELA)
        documentos = self._relatorios.extrair_proventos(
            str(fundo.fnet_id), inicio, reference_date, ticker
        )
        return [documento.provento for documento in documentos]

    def obter_patrimonio(
        self: "B3FundamentalRepository", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Retorna ``None``; patrimônio é fornecido pela CVM em fase seguinte."""
        return None

    def _resolver(
        self: "B3FundamentalRepository", ticker: str
    ) -> B3Fund | None:
        """Resolve e memoriza a identidade do fundo para o ticker."""
        chave = ticker.strip().upper()
        if chave not in self._fundos_cache:
            try:
                self._fundos_cache[chave] = self._fundos.find_by_ticker(chave)
            except Exception:  # resolução tolerante
                logger.warning(
                    "Falha ao resolver fundo B3 de %s", chave, exc_info=True
                )
                self._fundos_cache[chave] = None
        return self._fundos_cache[chave]


def _subtrair_meses(data: date, meses: int) -> date:
    """Subtrai um número de meses de uma data, ajustando o dia ao mês."""
    total = data.year * 12 + (data.month - 1) - meses
    ano, mes = divmod(total, 12)
    dia = min(data.day, monthrange(ano, mes + 1)[1])
    return date(ano, mes + 1, dia)
