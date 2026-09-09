"""Provedor de FFO do Fundamentus (metodologia ``SOURCE_REPORTED``).

O Fundamentus publica o FFO dos últimos 12 e 3 meses. O provedor isola o
acesso à página atrás de um loader e usa ``SOURCE_SCHEMA_VERSION`` para o
formato esperado da extração. Quando o FFO não é encontrado na página, o
provedor retorna ``None`` sem estimar o valor (RFC-007 §20/§21).
"""

import logging
from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from flowscope.domain.fii.analysis import FfoObservacao
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.fii.parsing import moeda_para_decimal

logger = logging.getLogger("flowscope")

#: Versão esperada da estrutura da página de detalhes do Fundamentus.
SOURCE_SCHEMA_VERSION = "2026-01"

#: Fonte registrada nos objetos de FFO produzidos pelo provedor.
FONTE_FUNDAMENTUS = "FUNDAMENTUS"

#: Metodologia de obtenção do FFO (reportado pela fonte).
METODOLOGIA = "SOURCE_REPORTED"

#: URL da página de detalhes do Fundamentus.
_BASE_URL = "https://www.fundamentus.com.br/detalhes.php"

#: TTL do cache da página de detalhes.
_TTL_DIAS = 7


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
    ffo_12m = None
    ffo_3m = None
    for linha in soup.find_all("tr"):
        celulas = [celula.get_text(" ", strip=True) for celula in linha.find_all("td")]
        if len(celulas) < 2:
            continue
        rotulo = _normalizar(celulas[0])
        if "ffo" not in rotulo:
            continue
        valor = _ler_valor(celulas[1])
        if valor is None:
            continue
        if "12 meses" in rotulo or "12m" in rotulo:
            ffo_12m = valor
        elif "3 meses" in rotulo or "3m" in rotulo:
            ffo_3m = valor
    if ffo_12m is None or ffo_3m is None:
        return None
    return FfoObservacao(
        ffo_12m=ffo_12m,
        ffo_3m=ffo_3m,
        fonte=FONTE_FUNDAMENTUS,
        metodologia=METODOLOGIA,
    )


def _ler_valor(texto: str) -> Decimal | None:
    """Interpreta o valor monetário de uma célula, ou ``None`` se inválido."""
    try:
        return moeda_para_decimal(texto)
    except InvalidOperation:
        return None


def _fetch_detalhes(ticker: str) -> str:
    """Baixa a página de detalhes do ticker no Fundamentus."""
    import requests

    url = f"{_BASE_URL}"
    resp = requests.get(url, params={"papel": ticker}, timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


class FundamentusProvider:
    """Fornece o FFO reportado de um ticker a partir do Fundamentus."""

    def __init__(
        self: "FundamentusProvider",
        loader: Callable[[str], str] | None = None,
        cache: CacheManager | None = None,
    ) -> None:
        """Inicializa o provedor com o loader da página e o cache."""
        self._loader = loader or _fetch_detalhes
        self._cache = cache

    def obter_ffo(
        self: "FundamentusProvider", ticker: str, reference_date: date
    ) -> FfoObservacao | None:
        """Extrai o FFO do ticker, usando cache quando disponível."""
        normalizado = ticker.strip().upper()
        html = self._carregar_detalhes(normalizado)
        if not html:
            return None
        try:
            return extrair_ffo(html)
        except Exception:  # página com estrutura inesperada
            logger.warning(
                "Falha ao extrair FFO de %s no Fundamentus", normalizado, exc_info=True
            )
            return None

    def _carregar_detalhes(self: "FundamentusProvider", ticker: str) -> str:
        """Carrega a página, usando o cache quando disponível."""
        if self._cache is None:
            return self._carregar_com_tolerancia(ticker)
        payload = self._cache.get_or_fetch(
            f"fundamentus_ffo_{ticker}",
            ttl_days=_TTL_DIAS,
            fetch_fn=lambda: {"conteudo": self._carregar_com_tolerancia(ticker)},
        )
        return str(payload.get("conteudo", ""))

    def _carregar_com_tolerancia(self: "FundamentusProvider", ticker: str) -> str:
        """Chama o loader, devolvendo vazio quando a aquisição falha."""
        try:
            conteudo = self._loader(ticker)
        except Exception:  # aquisição tolerante
            logger.warning("Falha ao carregar Fundamentus de %s", ticker, exc_info=True)
            return ""
        return conteudo or ""
