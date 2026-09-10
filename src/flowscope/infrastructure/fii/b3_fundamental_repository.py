"""Repositório fundamentalista apoiado na camada B3 (RFC-008).

Fornece nome, proventos e patrimônio a partir da identidade e dos documentos da
B3. O patrimônio usa o Informe Mensal Estruturado (B3) como fonte primária e a
CVM como fallback.
"""

import logging
from calendar import monthrange
from datetime import date

from flowscope.domain.b3 import B3Fund, B3InformeMensal
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
        patrimonio_source: object | None = None,
    ) -> None:
        """Inicializa o repositório com as fontes B3 e a fonte de patrimônio."""
        self._fundos = fund_repository or B3FundRepository()
        self._relatorios = reports_repository or B3ReportsRepository()
        self._patrimonio_source = patrimonio_source
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
        """Retorna o patrimônio consolidando B3 (primário) e CVM (fallback)."""
        b3 = self._obter_patrimonio_b3(ticker, reference_date)
        if b3 is not None:
            return b3
        return self._obter_patrimonio_cvm(ticker, reference_date)

    def _obter_patrimonio_b3(
        self: "B3FundamentalRepository", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Obtém o patrimônio do Informe Mensal Estruturado da B3."""
        extrair = getattr(self._relatorios, "extrair_informe", None)
        if not callable(extrair):
            return None
        fundo = self._resolver(ticker)
        if fundo is None:
            return None
        inicio = _subtrair_meses(reference_date, _MESES_JANELA)
        try:
            informe = extrair(
                str(fundo.fnet_id), inicio, reference_date, reference_date
            )
        except Exception:  # indisponibilidade da B3, distinta de ausência
            logger.warning(
                "Falha ao obter informe mensal B3 de %s", ticker, exc_info=True
            )
            return None
        return _informe_para_patrimonio(informe)

    def _obter_patrimonio_cvm(
        self: "B3FundamentalRepository", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Obtém o patrimônio da fonte CVM configurada."""
        if self._patrimonio_source is None:
            return None
        try:
            return self._patrimonio_source.patrimonio(ticker, reference_date)
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao obter patrimônio de %s", ticker, exc_info=True
            )
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


def _informe_para_patrimonio(
    informe: B3InformeMensal | None,
) -> PatrimonioFii | None:
    """Retorna uma observação de patrimônio a partir de um informe, ou ``None``."""
    if informe is None or informe.reference_date is None:
        return None
    if informe.patrimonio_liquido is None or informe.cotas_emitidas is None:
        return None
    return PatrimonioFii(
        reference_date=informe.reference_date,
        net_asset_value=informe.patrimonio_liquido,
        shares_outstanding=informe.cotas_emitidas,
        cotistas=informe.cotistas,
        fonte=informe.fonte,
        vp_cota=informe.valor_patrimonial_cota,
    )


def _subtrair_meses(data: date, meses: int) -> date:
    """Subtrai um número de meses de uma data, ajustando o dia ao mês."""
    total = data.year * 12 + (data.month - 1) - meses
    ano, mes = divmod(total, 12)
    dia = min(data.day, monthrange(ano, mes + 1)[1])
    return date(ano, mes + 1, dia)
