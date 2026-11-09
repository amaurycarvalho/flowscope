"""Modelo de domínio da série histórica de fechamento de um índice."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class IndexClose:
    """Fechamento diário de um índice."""

    date: date
    close: Decimal
