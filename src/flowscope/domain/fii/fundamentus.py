"""Modelo normalizado dos dados fundamentalistas do Fundamentus (RFC-011).

Reúne, em tipos do domínio (``Decimal``/``date``), os campos extraídos da
página de detalhes do Fundamentus para ações e FIIs, preservando também o
mapeamento bruto rótulo→valor para diagnóstico e evolução do parser.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

#: Tipo de ativo reconhecido pelo Fundamentus.
TIPO_ACAO = "acao"
TIPO_FII = "fii"

#: Discriminador do rótulo do campo de ticker na página do Fundamentus.
DISCRIMINADOR_PAPEL = "papel"
DISCRIMINADOR_FII = "fii"


@dataclass(frozen=True)
class AtivoFundamental:
    """Dados fundamentalistas normalizados de uma ação ou FII."""

    ticker: str
    tipo: str
    discriminador: str | None = None
    especie: str | None = None
    setor: str | None = None
    subsetor: str | None = None
    segmento: str | None = None
    gestao: str | None = None
    nome: str | None = None
    cotacao: Decimal | None = None
    data_ultima_cotacao: date | None = None
    min_52_sem: Decimal | None = None
    max_52_sem: Decimal | None = None
    volume_medio_2m: Decimal | None = None
    oscilacoes: dict[str, Decimal] = field(default_factory=dict)
    indicadores: dict[str, Decimal] = field(default_factory=dict)
    balanco: dict[str, Decimal] = field(default_factory=dict)
    demonstrativos_12m: dict[str, Decimal] = field(default_factory=dict)
    demonstrativos_3m: dict[str, Decimal] = field(default_factory=dict)
    composicao_ativos: dict[str, Decimal] = field(default_factory=dict)
    imoveis: dict[str, Decimal | int | None] = field(default_factory=dict)
    raw: dict[str, str] = field(default_factory=dict)

    def eh_fii(self: "AtivoFundamental") -> bool:
        """Indica se o ativo é um Fundo de Investimento Imobiliário."""
        return self.tipo == TIPO_FII
