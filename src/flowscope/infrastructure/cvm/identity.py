"""Resolução de ticker para a identidade regulatória CVM (RFC-009 §7)."""

import logging
from collections.abc import Callable

from flowscope.domain.cvm import FundIdentity, normalizar_cnpj
from flowscope.infrastructure.b3.fund_repository import B3FundRepository

logger = logging.getLogger("flowscope")

#: Quantidade de dígitos de um CNPJ válido.
_DIGITOS_CNPJ = 14


def resolver_identidade(
    ticker: str,
    fund_repository: B3FundRepository | None = None,
    code_cvm_resolver: Callable[[str], str | None] | None = None,
) -> FundIdentity | None:
    """Resolve a identidade CVM do ticker a partir da B3 e do cadastro CVM."""
    chave = ticker.strip().upper()
    try:
        fundo = (fund_repository or B3FundRepository()).find_by_ticker(chave)
    except Exception:  # resolução tolerante
        logger.warning("Falha ao resolver fundo B3 de %s", chave, exc_info=True)
        return None
    if fundo is None:
        return None
    cnpj = normalizar_cnpj(fundo.trading_name)
    if len(cnpj) != _DIGITOS_CNPJ:
        return None
    codigo = None
    if code_cvm_resolver is not None:
        try:
            codigo = code_cvm_resolver(chave)
        except Exception:  # cadastro CVM opcional
            logger.warning(
                "Falha ao resolver codeCVM de %s", chave, exc_info=True
            )
    return FundIdentity(
        ticker=chave,
        cnpj_fundo_classe=cnpj,
        codigo_cvm=codigo,
        id_fnet=fundo.fnet_id,
        name=fundo.name,
    )
