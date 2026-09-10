"""Modelos normalizados da aquisição CVM (RFC-009 §7/§23)."""

import re
from dataclasses import dataclass
from datetime import date

_DIGITOS_RE = re.compile(r"\D")


def normalizar_cnpj(valor: str | None) -> str:
    """Remove a pontuação de um CNPJ, mantendo apenas os dígitos."""
    return _DIGITOS_RE.sub("", valor or "")


@dataclass(frozen=True)
class FundIdentity:
    """Identidade regulatória de um fundo, resolvida a partir do ticker."""

    ticker: str
    cnpj_fundo_classe: str
    codigo_cvm: str | None = None
    id_fnet: str | None = None
    name: str = ""


@dataclass(frozen=True)
class MonthlyReport:
    """Registro selecionado do Informe Mensal Estruturado da CVM."""

    ticker: str
    cnpj_fundo_classe: str
    reference_date: date
    raw_rows: dict
    source_file: str
    source_hash: str
    is_latest: bool = True
    source_version: str | None = None
    received_at: str | None = None
