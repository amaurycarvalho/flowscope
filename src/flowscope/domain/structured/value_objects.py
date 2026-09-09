"""Objetos de valor do domínio de dados estruturados da B3."""

import re
from decimal import Decimal
from enum import Enum

_CNPJ_RE = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
_ISIN_RE = re.compile(r"^BR[A-Z0-9]{10}$")
_MONETARY_RE = re.compile(r"[^\d,.-]")
_CODIGO_CVM_RE = re.compile(r"^\d{1,6}$")


def _parse_monetary(value: str) -> Decimal:
    """Interpreta uma string monetária brasileira como ``Decimal``."""
    cleaned = _MONETARY_RE.sub("", value)
    if "," in cleaned:
        int_part, _, dec_part = cleaned.partition(",")
        dec_part = dec_part.replace(",", "")
        cleaned = f"{int_part.replace('.', '')}.{dec_part}"
    elif "." in cleaned:
        cleaned = cleaned.replace(",", "")
    else:
        cleaned = cleaned.replace(".", "")
    return Decimal(cleaned or "0")


class CNPJ:
    """CNPJ validado no formato ``XX.XXX.XXX/XXXX-XX``."""

    def __init__(self: "CNPJ", value: str) -> None:
        """Valida o formato e armazena o CNPJ."""
        value = value.strip()
        if not _CNPJ_RE.match(value):
            raise ValueError(f"CNPJ inválido: {value!r}")
        self._value = value

    @property
    def value(self: "CNPJ") -> str:
        """Retorna o CNPJ formatado."""
        return self._value

    def __eq__(self: "CNPJ", other: object) -> bool:
        """Compara igualdade com outro CNPJ."""
        if not isinstance(other, CNPJ):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "CNPJ") -> int:
        """Retorna o hash baseado no valor do CNPJ."""
        return hash(self._value)

    def __repr__(self: "CNPJ") -> str:
        """Representação textual do CNPJ."""
        return f"CNPJ({self._value})"


class ISIN:
    """Código ISIN validado com 12 caracteres e prefixo ``BR``."""

    def __init__(self: "ISIN", value: str) -> None:
        """Inicializa o ISIN, rejeitando códigos fora do padrão esperado."""
        value = value.strip().upper()
        if not _ISIN_RE.match(value):
            raise ValueError(f"ISIN inválido: {value!r}")
        self._value = value

    @property
    def value(self: "ISIN") -> str:
        """Retorna o ISIN normalizado."""
        return self._value

    def __eq__(self: "ISIN", other: object) -> bool:
        """Compara igualdade com outro ISIN."""
        if not isinstance(other, ISIN):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "ISIN") -> int:
        """Retorna o hash baseado no valor do ISIN."""
        return hash(self._value)

    def __repr__(self: "ISIN") -> str:
        """Representação textual do ISIN."""
        return f"ISIN({self._value})"


class ValorProvento:
    """Valor monetário de um provento normalizado como ``Decimal``.

    Aceita strings no formato monetário brasileiro (ex.: ``R$ 1.234,56``) ou
    valores numéricos já fornecidos como ``Decimal``.
    """

    def __init__(self: "ValorProvento", value: Decimal | str) -> None:
        """Inicializa o valor do provento a partir de uma string ou Decimal."""
        if isinstance(value, str):
            self._value = _parse_monetary(value)
        else:
            self._value = value

    @property
    def value(self: "ValorProvento") -> Decimal:
        """Retorna o valor do provento em Decimal."""
        return self._value

    def __eq__(self: "ValorProvento", other: object) -> bool:
        """Compara igualdade com outro valor de provento."""
        if not isinstance(other, ValorProvento):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "ValorProvento") -> int:
        """Retorna o hash baseado no valor do provento."""
        return hash(self._value)

    def __repr__(self: "ValorProvento") -> str:
        """Representação textual do valor do provento."""
        return f"ValorProvento({self._value})"


class CodeCVM:
    """Código CVM da empresa listada, validado como campo numérico da B3."""

    def __init__(self: "CodeCVM", value: str) -> None:
        """Valida o formato numérico e armazena o código CVM."""
        value = value.strip()
        if not _CODIGO_CVM_RE.match(value):
            raise ValueError(f"Código CVM inválido: {value!r}")
        self._value = value

    @property
    def value(self: "CodeCVM") -> str:
        """Retorna o código CVM normalizado."""
        return self._value

    def __str__(self: "CodeCVM") -> str:
        """Retorna o código CVM como string."""
        return self._value

    def __eq__(self: "CodeCVM", other: object) -> bool:
        """Compara igualdade com outro código CVM."""
        if not isinstance(other, CodeCVM):
            return NotImplemented
        return self._value == other._value

    def __hash__(self: "CodeCVM") -> int:
        """Retorna o hash baseado no valor do código CVM."""
        return hash(self._value)

    def __repr__(self: "CodeCVM") -> str:
        """Representação textual do código CVM."""
        return f"CodeCVM({self._value})"


class CategoriaMaterialFact(Enum):
    """Categorias de documentos do endpoint ``GetMaterialFacts`` da B3."""

    ASSEMBLEIAS = "1"
    AVISO_ACIONISTAS = "3"
    FATOS_RELEVANTES = "4"
    AVISO_DEBENTURISTAS = "48"
    RELATORIO_PROVENTOS = "107"

    def __str__(self: "CategoriaMaterialFact") -> str:
        """Retorna o código numérico da categoria como string."""
        return self.value


CategoriaDocumento = CategoriaMaterialFact
