"""Repositório de identidade de fundos na B3 (RFC-008 §3)."""

from flowscope.domain.b3 import B3Fund
from flowscope.infrastructure.b3.funds_client import B3FundosClient


class B3FundRepository:
    """Resolve tickers para a identidade normalizada do fundo na B3."""

    def __init__(
        self: "B3FundRepository", client: B3FundosClient | None = None
    ) -> None:
        """Inicializa o repositório com o cliente de fundos informado."""
        self._client = client or B3FundosClient()

    def find_by_ticker(self: "B3FundRepository", ticker: str) -> B3Fund | None:
        """Retorna a identidade do fundo do ticker, ou ``None`` sem dados."""
        candidato = self._client.selecionar_candidato(ticker)
        if not candidato or not candidato.get("id"):
            return None
        id_main = candidato.get("idMain")
        return B3Fund(
            ticker=ticker.strip().upper(),
            fnet_id=str(candidato["id"]),
            primary_id=str(id_main) if id_main is not None else None,
            name=str(candidato.get("fundName") or ""),
            trading_name=candidato.get("tradingName"),
        )
