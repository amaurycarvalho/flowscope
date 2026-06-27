from decimal import Decimal


class Price:
    def __init__(self, value: Decimal | str | float | int):
        if isinstance(value, str):
            value = value.replace(",", ".")
        self._value = Decimal(str(value)) if not isinstance(value, Decimal) else value

    @property
    def value(self) -> Decimal:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, Price):
            return NotImplemented
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Price({self._value})"


class Volume:
    def __init__(self, value: int):
        if value < 0:
            raise ValueError(f"Volume não pode ser negativo: {value}")
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, Volume):
            return NotImplemented
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Volume({self._value})"


class Delta:
    def __init__(self, value: float):
        self._value = float(value)

    @property
    def value(self) -> float:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, Delta):
            return NotImplemented
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Delta({self._value})"


class Ticker:
    _VALID_SEGMENTS = {"CASH", "ETF", "FUTURE", "OPTION", "BDR", "UNIT", "INDEX"}

    def __init__(self, value: str):
        value = value.strip().upper()
        if not value:
            raise ValueError("Ticker não pode ser vazio")
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, Ticker):
            return NotImplemented
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Ticker({self._value})"
