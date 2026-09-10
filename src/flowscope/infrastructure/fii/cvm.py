"""Adapter CVM para patrimônio, cotas e cotistas de FIIs.

Lê o Informe Mensal Estruturado da CVM (dataset ``INF_MENSAL``) e resolve o
informe mais recente disponível até a data de referência. O esquema de colunas
é versionado em ``SOURCE_SCHEMA_VERSION``; mudanças na fonte exigem atualização
explícita do adapter (RFC-007 §52/§53).
"""

import csv
import io
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.cvm.patrimonio import para_patrimonio
from flowscope.infrastructure.cvm.schema import (
    CvmSchemaError,
    mapear_linha,
    validar_schema,
)
from flowscope.infrastructure.fii.parsing import data_brasileira, moeda_para_decimal

logger = logging.getLogger("flowscope")

#: Versão do esquema de colunas do Informe Mensal Estruturado da CVM.
SOURCE_SCHEMA_VERSION = "2026-01"

#: Fonte registrada nos objetos de patrimônio produzidos pelo adapter.
FONTE_CVM = "CVM"

_CNPJ_RE = re.compile(r"[^\d]")
_TTL_DIAS = 30


@dataclass(frozen=True)
class _Informe:
    """Linha normalizada de um informe mensal de um fundo."""

    cnpj: str
    data_competencia: date
    patrimonio_liquido: Decimal
    cotas: Decimal
    cotistas: int | None


def _cnpj_digitos(cnpj: str) -> str:
    """Remove pontuação de um CNPJ para comparação."""
    return _CNPJ_RE.sub("", cnpj)


def parse_informe_mensal(conteudo: str) -> list[_Informe]:
    """Lê o CSV estruturado do informe mensal e devolve as linhas válidas.

    Linhas com dados inválidos são ignoradas. A ausência de colunas esperadas
    no cabeçalho levanta ``CvmSchemaError`` (RFC-007 §52).
    """
    reader = csv.DictReader(io.StringIO(conteudo), delimiter=";")
    if reader.fieldnames is None:
        return []
    colunas = {coluna.strip() for coluna in reader.fieldnames}
    validar_schema(colunas)

    informes: list[_Informe] = []
    for linha in reader:
        informe = _linha_para_informe(linha, colunas)
        if informe is not None:
            informes.append(informe)
    return informes


def _linha_para_informe(linha: dict[str, str], colunas: object) -> _Informe | None:
    """Monta um informe a partir de uma linha do CSV, ignorando dados inválidos."""
    canonica = mapear_linha(linha, colunas)
    cnpj = _cnpj_digitos(canonica.get("cnpj") or "")
    if not cnpj:
        return None
    try:
        data = _parse_competencia(canonica.get("competencia"))
        patrimonio = moeda_para_decimal(canonica.get("patrimonio") or "0")
        cotas = moeda_para_decimal(canonica.get("cotas") or "0")
    except (InvalidOperation, ValueError, KeyError):
        return None
    cotistas = _ler_cotistas(canonica.get("cotistas") or "")
    return _Informe(
        cnpj=cnpj,
        data_competencia=data,
        patrimonio_liquido=patrimonio,
        cotas=cotas,
        cotistas=cotistas,
    )


def _parse_competencia(valor: object) -> date:
    """Interpreta a competência em formato brasileiro ou ISO."""
    if not valor:
        raise ValueError("competência ausente")
    texto = str(valor).strip()
    if "/" in texto:
        return data_brasileira(texto)
    partes = texto[:10].split("-")
    return date(int(partes[0]), int(partes[1]), int(partes[2]))


def _ler_cotistas(valor: str) -> int | None:
    """Interpreta o número de cotistas, retornando ``None`` quando inválido."""
    limpo = valor.strip()
    if not limpo:
        return None
    try:
        return int(limpo)
    except ValueError:
        return None


class CvmFiiAdapter:
    """Fornece patrimônio de FIIs a partir dos informes mensais da CVM."""

    def __init__(
        self: "CvmFiiAdapter",
        loader: Callable[[int], str] | None = None,
        resolver_cnpj: Callable[[str], str | None] | None = None,
        cache: CacheManager | None = None,
        repository: object | None = None,
    ) -> None:
        """Inicializa o adapter com o carregador, o resolvedor, o cache e o repositório."""
        self._loader = loader
        self._resolver_cnpj = resolver_cnpj or (lambda _ticker: None)
        self._cache = cache
        self._repository = repository

    def patrimonio(
        self: "CvmFiiAdapter", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Resolve o patrimônio mais recente do ticker até a referência."""
        if self._repository is not None:
            return self._patrimonio_do_repositorio(ticker, reference_date)
        cnpj = self._resolver_cnpj(ticker.strip().upper())
        if cnpj is None:
            return None
        anos = {reference_date.year, reference_date.year - 1}
        for ano in sorted(anos, reverse=True):
            conteudo = self._carregar_ano(ano)
            if not conteudo:
                continue
            try:
                informes = parse_informe_mensal(conteudo)
            except CvmSchemaError:
                logger.warning(
                    "Esquema CVM inesperado para o ano %s", ano, exc_info=True
                )
                continue
            candidatos = [
                informe
                for informe in informes
                if informe.cnpj == cnpj and informe.data_competencia <= reference_date
            ]
            if not candidatos:
                continue
            melhor = max(candidatos, key=lambda informe: informe.data_competencia)
            return PatrimonioFii(
                reference_date=melhor.data_competencia,
                net_asset_value=melhor.patrimonio_liquido,
                shares_outstanding=melhor.cotas,
                cotistas=melhor.cotistas,
                fonte=FONTE_CVM,
            )
        return None

    def _patrimonio_do_repositorio(
        self: "CvmFiiAdapter", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Obtém o patrimônio delegando ao repositório CVM informado."""
        cnpj = self._resolver_cnpj(ticker.strip().upper())
        if cnpj is None:
            return None
        report = self._repository.get(cnpj, reference_date, ticker=ticker)
        if report is None:
            return None
        return para_patrimonio(report)

    def _carregar_ano(self: "CvmFiiAdapter", ano: int) -> str:
        """Carrega o dataset anual, usando o cache quando disponível."""
        if self._loader is None:
            return ""
        if self._cache is None:
            return self._carregar_com_tolerancia(ano)
        payload = self._cache.get_or_fetch(
            f"cvm_informe_mensal_{ano}",
            ttl_days=_TTL_DIAS,
            fetch_fn=lambda: {"conteudo": self._carregar_com_tolerancia(ano)},
        )
        return str(payload.get("conteudo", ""))

    def _carregar_com_tolerancia(self: "CvmFiiAdapter", ano: int) -> str:
        """Chama o loader, devolvendo vazio quando a aquisição falha."""
        try:
            conteudo = self._loader(ano)
        except Exception:  # aquisição tolerante
            logger.warning("Falha ao carregar informe CVM de %s", ano, exc_info=True)
            return ""
        return conteudo or ""
