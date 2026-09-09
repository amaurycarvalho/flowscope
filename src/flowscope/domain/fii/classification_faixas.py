"""Faixas determinísticas de classificação previstas na RFC-006.

Inclui a classificação da tendência do FFO (momentum) e as faixas por número
de cotistas e por tamanho patrimonial. Os limiares são fixos e explícitos,
permitindo auditoria sem interpretação.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


#: Limiares padrão da classificação da tendência do FFO (RFC-006 §12).
class ConfiguracaoMomentum:
    """Limiares configuráveis da tendência do FFO.

    A configuração é externa e versionada; alteração de limiares não ocorre de
    forma silenciosa. Os valores padrão espelham a RFC-006 §12.
    """

    forte_alta = Decimal("0.20")
    alta = Decimal("0.05")
    estavel_inferior = Decimal("-0.05")
    forte_queda = Decimal("-0.20")


@dataclass(frozen=True)
class FaixasCotistas:
    """Faixas por número de cotistas (RFC-006)."""

    micro_maximo: int = 250
    muito_pequeno_maximo: int = 1000
    pequeno_maximo: int = 5000
    medio_maximo: int = 35000
    grande_maximo: int = 65000
    muito_grande_maximo: int = 100000


@dataclass(frozen=True)
class FaixasPatrimonio:
    """Faixas por patrimônio líquido em reais (RFC-006)."""

    micro_maximo: Decimal = Decimal(50000000)
    pequeno_maximo: Decimal = Decimal(100000000)
    medio_maximo: Decimal = Decimal(250000000)
    grande_maximo: Decimal = Decimal(500000000)
    muito_grande_maximo: Decimal = Decimal(1000000000)


class TendenciaFfo(Enum):
    """Classificação textual da tendência recente do FFO."""

    FORTE_ALTA = "FORTE_ALTA"
    ALTA = "ALTA"
    ESTAVEL = "ESTAVEL"
    QUEDA = "QUEDA"
    FORTE_QUEDA = "FORTE_QUEDA"


class ClasseCotistas(Enum):
    """Classe por número de cotistas."""

    MICRO = "MICRO"
    MUITO_PEQUENO = "MUITO_PEQUENO"
    PEQUENO = "PEQUENO"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"
    MUITO_GRANDE = "MUITO_GRANDE"
    GIGANTE = "GIGANTE"


class ClassePatrimonio(Enum):
    """Classe por tamanho do patrimônio líquido."""

    MICRO = "MICRO"
    PEQUENO = "PEQUENO"
    MEDIO = "MEDIO"
    GRANDE = "GRANDE"
    MUITO_GRANDE = "MUITO_GRANDE"
    GIGANTE = "GIGANTE"


def classificar_tendencia_ffo(
    mudanca: Decimal, faixas: ConfiguracaoMomentum | None = None
) -> TendenciaFfo:
    """Classifica a mudança relativa do FFO em uma tendência determinística."""
    conf = faixas or ConfiguracaoMomentum()
    if mudanca >= conf.forte_alta:
        return TendenciaFfo.FORTE_ALTA
    if mudanca >= conf.alta:
        return TendenciaFfo.ALTA
    if mudanca > conf.estavel_inferior:
        return TendenciaFfo.ESTAVEL
    if mudanca >= conf.forte_queda:
        return TendenciaFfo.QUEDA
    return TendenciaFfo.FORTE_QUEDA


def classificar_cotistas(
    cotistas: int, faixas: FaixasCotistas | None = None
) -> ClasseCotistas:
    """Classifica o número de cotistas em uma das faixas determinísticas."""
    conf = faixas or FaixasCotistas()
    if cotistas <= conf.micro_maximo:
        return ClasseCotistas.MICRO
    if cotistas <= conf.muito_pequeno_maximo:
        return ClasseCotistas.MUITO_PEQUENO
    if cotistas <= conf.pequeno_maximo:
        return ClasseCotistas.PEQUENO
    if cotistas <= conf.medio_maximo:
        return ClasseCotistas.MEDIO
    if cotistas <= conf.grande_maximo:
        return ClasseCotistas.GRANDE
    if cotistas <= conf.muito_grande_maximo:
        return ClasseCotistas.MUITO_GRANDE
    return ClasseCotistas.GIGANTE


def classificar_patrimonio(
    patrimonio: Decimal, faixas: FaixasPatrimonio | None = None
) -> ClassePatrimonio:
    """Classifica o patrimônio líquido em uma das faixas determinísticas."""
    conf = faixas or FaixasPatrimonio()
    if patrimonio < conf.micro_maximo:
        return ClassePatrimonio.MICRO
    if patrimonio <= conf.pequeno_maximo:
        return ClassePatrimonio.PEQUENO
    if patrimonio <= conf.medio_maximo:
        return ClassePatrimonio.MEDIO
    if patrimonio <= conf.grande_maximo:
        return ClassePatrimonio.GRANDE
    if patrimonio <= conf.muito_grande_maximo:
        return ClassePatrimonio.MUITO_GRANDE
    return ClassePatrimonio.GIGANTE
