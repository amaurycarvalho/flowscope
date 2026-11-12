"""Repositório de identidade de fundos na B3 (RFC-008 §3)."""

import logging
from dataclasses import dataclass

from flowscope.domain.b3 import B3Fund
from flowscope.domain.cvm import normalizar_cnpj
from flowscope.infrastructure.b3.fund_identity_store import (
    FundIdentityRecord,
    JsonFundIdentityStore,
)
from flowscope.infrastructure.b3.funds_client import (
    B3FundosClient,
    ResolucaoCandidato,
)

_DIGITOS_CNPJ = 14

logger = logging.getLogger("flowscope")


@dataclass(frozen=True)
class _ResolucaoCompativel:
    """Adapta clientes antigos, sem ``obter_candidato``, ao novo contrato."""

    candidato: dict | None
    completa: bool
    tipo_fund: str | None = None


class B3FundRepository:
    """Resolve tickers para a identidade normalizada do fundo na B3."""

    def __init__(
        self: "B3FundRepository",
        client: B3FundosClient | None = None,
        identity_store: JsonFundIdentityStore | None = None,
    ) -> None:
        """Inicializa o repositório com o cliente e o store de identidade."""
        self._client = client or B3FundosClient()
        self._identity_store = identity_store

    def tipo_fundo(self: "B3FundRepository", ticker: str) -> str | None:
        """Retorna o tipo de fundo do ticker na B3, ou ``None`` sem dados."""
        return self._client.tipo_fundo(ticker)

    def find_by_ticker(self: "B3FundRepository", ticker: str) -> B3Fund | None:
        """Retorna a identidade do fundo do ticker, ou ``None`` sem dados.

        Uma listagem completa prevalece sobre a identidade persistida: se o
        ticker não estiver nela, retorna ``None``. Em falha ou listagem
        incompleta, recorre ao registro persistido, quando existir.
        """
        chave = ticker.strip().upper()
        try:
            resolucao = self._resolver(chave)
        except Exception:  # resolução tolerante
            return self._identidade_persistida(chave)
        fundo = self._fundo_de_resolucao(chave, resolucao)
        if fundo is not None:
            self._persistir(fundo, resolucao.tipo_fund)
            return fundo
        if resolucao.completa:
            return None
        return self._identidade_persistida(chave)

    def resolver_code_cvm(
        self: "B3FundRepository", ticker: str
    ) -> str | None:
        """Resolve o ``codeCVM`` do ticker pelo cliente B3, de forma tolerante."""
        obter = getattr(self._client, "resolver_code_cvm", None)
        if not callable(obter):
            return None
        try:
            return obter(ticker.strip().upper())
        except Exception:  # resolução tolerante
            logger.warning(
                "Falha ao resolver codeCVM de %s", ticker, exc_info=True
            )
            return None

    def obter_nome_negociacao(
        self: "B3FundRepository", ticker: str
    ) -> str | None:
        """Retorna o nome de exibição da empresa listada (ação/BDR), ou ``None``.

        Usa a identidade B3 já consultada (``GetInitialCompanies``) sem nova
        fonte de dados.
        """
        return self._client.obter_nome_negociacao(ticker)

    def _resolver(
        self: "B3FundRepository", ticker: str
    ) -> ResolucaoCandidato | _ResolucaoCompativel:
        """Resolve o candidato usando o novo contrato ou um cliente legado."""
        obter = getattr(self._client, "obter_candidato", None)
        if callable(obter):
            return obter(ticker)
        candidato = self._client.selecionar_candidato(ticker)
        return _ResolucaoCompativel(candidato, bool(candidato))

    def _fundo_de_resolucao(
        self: "B3FundRepository",
        ticker: str,
        resolucao: ResolucaoCandidato | _ResolucaoCompativel,
    ) -> B3Fund | None:
        """Monta o ``B3Fund`` a partir do candidato selecionado."""
        candidato = resolucao.candidato
        if not candidato or not candidato.get("id"):
            return None
        id_main = candidato.get("idMain")
        return B3Fund(
            ticker=ticker,
            fnet_id=str(candidato["id"]),
            primary_id=str(id_main) if id_main is not None else None,
            name=str(candidato.get("fundName") or ""),
            trading_name=candidato.get("tradingName"),
        )

    def _persistir(
        self: "B3FundRepository", fundo: B3Fund, type_fund: str | None
    ) -> None:
        """Grava a identidade resolvida no store persistente, se configurado."""
        if self._identity_store is None:
            return
        cnpj = normalizar_cnpj(fundo.trading_name)
        self._identity_store.salvar(
            fundo.ticker,
            id_fnet=fundo.fnet_id,
            primary_id=fundo.primary_id,
            name=fundo.name,
            trading_name=fundo.trading_name,
            cnpj=cnpj if len(cnpj) == _DIGITOS_CNPJ else None,
            type_fund=type_fund,
        )

    def _identidade_persistida(
        self: "B3FundRepository", ticker: str
    ) -> B3Fund | None:
        """Reconstrói o ``B3Fund`` a partir do registro persistido do ticker."""
        if self._identity_store is None:
            return None
        registro = self._identity_store.obter(ticker)
        if registro is None:
            return None
        return _fundo_do_registro(registro)


def _fundo_do_registro(registro: FundIdentityRecord) -> B3Fund:
    """Reconstrói a identidade normalizada a partir do registro persistido."""
    return B3Fund(
        ticker=registro.ticker,
        fnet_id=registro.id_fnet,
        primary_id=registro.primary_id,
        name=registro.name,
        trading_name=registro.cnpj or registro.trading_name,
    )
