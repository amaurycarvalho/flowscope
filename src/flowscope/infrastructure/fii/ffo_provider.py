"""Adaptador de compatibilidade do FFO via Fundamentus.

Mantém a extração do FFO 12m/3m (metodologia ``SOURCE_REPORTED``) sobre o
provider completo do Fundamentus (RFC-011), preservando a interface
``obter_ffo`` consumida pelo ``FfoProvider``.
"""

import logging
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup, Tag

from flowscope.domain.fii.analysis import FfoObservacao
from flowscope.infrastructure.fii.fundamentus.provider import (
    FONTE_FUNDAMENTUS,
)
from flowscope.infrastructure.fii.fundamentus.provider import (
    FundamentusProvider as _FundamentusProvider,
)
from flowscope.infrastructure.fii.parsing import moeda_para_decimal

logger = logging.getLogger("flowscope")

#: Versão esperada da estrutura da página de detalhes do Fundamentus.
SOURCE_SCHEMA_VERSION = "2026-01"

#: Metodologia de obtenção do FFO (reportado pela fonte).
METODOLOGIA = "SOURCE_REPORTED"

__all__ = [
    "FONTE_FUNDAMENTUS",
    "METODOLOGIA",
    "SOURCE_SCHEMA_VERSION",
    "FundamentusProvider",
    "extrair_ffo",
]


def _normalizar(texto: str) -> str:
    """Normaliza o texto de uma célula para comparação."""
    return " ".join(texto.split()).lower()


def extrair_ffo(html: str) -> FfoObservacao | None:
    """Extrai o FFO 12m/3m da página de detalhes do Fundamentus.

    Procura linhas de tabela cuja primeira célula contém ``FFO`` e distingue o
    período pelos rótulos ``12 meses`` e ``3 meses``. Sem o par completo a
    extração retorna ``None``.
    """
    soup = BeautifulSoup(html, "html.parser")
    valores = _coletar_ffo(soup)
    if valores is None:
        return None
    ffo_12m, ffo_3m = valores
    return FfoObservacao(
        ffo_12m=ffo_12m,
        ffo_3m=ffo_3m,
        fonte=FONTE_FUNDAMENTUS,
        metodologia=METODOLOGIA,
    )


def _coletar_ffo(soup: BeautifulSoup) -> tuple[Decimal, Decimal] | None:
    """Percorre as linhas e retorna o par (FFO 12m, FFO 3m), se completo."""
    ffo_12m = None
    ffo_3m = None
    for linha in soup.find_all("tr"):
        rotulo, valor = _rotulo_e_valor(linha)
        if rotulo is None or valor is None:
            continue
        if _eh_12_meses(rotulo):
            ffo_12m = valor
        elif _eh_3_meses(rotulo):
            ffo_3m = valor
    if ffo_12m is None or ffo_3m is None:
        return None
    return ffo_12m, ffo_3m


def _rotulo_e_valor(linha: Tag) -> tuple[str | None, Decimal | None]:
    """Retorna o rótulo normalizado e o valor de uma linha de FFO."""
    celulas = [celula.get_text(" ", strip=True) for celula in linha.find_all("td")]
    if len(celulas) < 2:
        return None, None
    rotulo = _normalizar(celulas[0])
    if "ffo" not in rotulo:
        return None, None
    return rotulo, _ler_valor(celulas[1])


def _eh_12_meses(rotulo: str) -> bool:
    """Indica se o rótulo se refere à janela de 12 meses."""
    return "12 meses" in rotulo or "12m" in rotulo


def _eh_3_meses(rotulo: str) -> bool:
    """Indica se o rótulo se refere à janela de 3 meses."""
    return "3 meses" in rotulo or "3m" in rotulo


def _ler_valor(texto: str) -> Decimal | None:
    """Interpreta o valor monetário de uma célula, ou ``None`` se inválido."""
    try:
        return moeda_para_decimal(texto)
    except InvalidOperation:
        return None


class FundamentusProvider(_FundamentusProvider):
    """Provider de compatibilidade que expõe ``obter_ffo``."""

    def obter_ffo(
        self: "FundamentusProvider", ticker: str, reference_date: date
    ) -> FfoObservacao | None:
        """Extrai o FFO do ticker, retornando ``None`` quando indisponível."""
        normalizado = ticker.strip().upper()
        try:
            html = self._carregar(normalizado)
        except Exception:  # aquisição tolerante para o port FfoProvider
            logger.warning(
                "Falha ao carregar Fundamentus de %s", normalizado, exc_info=True
            )
            return None
        if not html:
            return None
        try:
            return extrair_ffo(html)
        except Exception:  # página com estrutura inesperada
            logger.warning(
                "Falha ao extrair FFO de %s no Fundamentus", normalizado, exc_info=True
            )
            return None
