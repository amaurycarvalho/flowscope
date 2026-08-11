"""Objetos de valor do domínio do FlowScope."""

from decimal import Decimal
from typing import ClassVar


class Price:
    """Preço normalizado como valor decimal."""

    def __init__(self: "Price", value: Decimal | str | float) -> None:
        """Inicializa o preço a partir de um valor decimal, string ou float."""
        if isinstance(value, str):
            value = value.replace(",", ".")
        self._value = Decimal(str(value)) if not isinstance(value, Decimal) else value

    @property
    def value(self: "Price") -> Decimal:
        """Retorna o preço em Decimal."""
        return self._value

    def __eq__(self: "Price", other: object) -> bool:
        """Compara igualdade com outro preço."""
        if not isinstance(other, Price):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "Price") -> int:
        """Retorna o hash baseado no valor do preço."""
        return hash(self._value)

    def __repr__(self: "Price") -> str:
        """Representação textual do preço."""
        return f"Price({self._value})"


class Volume:
    """Volume de negociação, sempre não negativo."""

    def __init__(self: "Volume", value: int) -> None:
        """Inicializa o volume, rejeitando valores negativos."""
        if value < 0:
            raise ValueError(f"Volume não pode ser negativo: {value}")
        self._value = value

    @property
    def value(self: "Volume") -> int:
        """Retorna o volume em inteiro."""
        return self._value

    def __eq__(self: "Volume", other: object) -> bool:
        """Compara igualdade com outro volume."""
        if not isinstance(other, Volume):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "Volume") -> int:
        """Retorna o hash baseado no valor do volume."""
        return hash(self._value)

    def __repr__(self: "Volume") -> str:
        """Representação textual do volume."""
        return f"Volume({self._value})"


class Delta:
    """Variação (delta) representada como float."""

    def __init__(self: "Delta", value: float) -> None:
        """Inicializa o delta a partir de um valor numérico."""
        self._value = float(value)

    @property
    def value(self: "Delta") -> float:
        """Retorna o delta em float."""
        return self._value

    def __eq__(self: "Delta", other: object) -> bool:
        """Compara igualdade com outro delta."""
        if not isinstance(other, Delta):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "Delta") -> int:
        """Retorna o hash baseado no valor do delta."""
        return hash(self._value)

    def __repr__(self: "Delta") -> str:
        """Representação textual do delta."""
        return f"Delta({self._value})"


class Ticker:
    """Ticker de um ativo com segmento de negociação válido."""

    _VALID_SEGMENTS: ClassVar[set[str]] = {"CASH", "ETF", "FUTURE", "OPTION", "BDR", "UNIT", "INDEX"}

    def __init__(self: "Ticker", value: str) -> None:
        """Inicializa o ticker normalizando maiúsculas e espaços."""
        value = value.strip().upper()
        if not value:
            raise ValueError("Ticker não pode ser vazio")
        self._value = value

    @property
    def value(self: "Ticker") -> str:
        """Retorna o ticker normalizado."""
        return self._value

    def __eq__(self: "Ticker", other: object) -> bool:
        """Compara igualdade com outro ticker."""
        if not isinstance(other, Ticker):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "Ticker") -> int:
        """Retorna o hash baseado no valor do ticker."""
        return hash(self._value)

    def __repr__(self: "Ticker") -> str:
        """Representação textual do ticker."""
        return f"Ticker({self._value})"
