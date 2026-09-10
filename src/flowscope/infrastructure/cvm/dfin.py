"""Aquisição das Demonstrações Financeiras (DFIN) da CVM (RFC-010 §10).

Fornece o resultado reportado do fundo por competência, usado para reconciliar
o FFO calculado pelo motor determinístico.
"""

import csv
import io
import logging
from datetime import date
from decimal import Decimal

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.infrastructure.cvm.datasets import (
    CvmDatasetDownloader,
    parse_data,
    parse_decimal,
)
from flowscope.infrastructure.cvm.schema import (
    mapear_com_aliases,
    tem_alias,
    validar_aliases,
)

logger = logging.getLogger("flowscope")

#: Diretório oficial das Demonstrações Financeiras de FIIs.
CVM_DFIN_URL = "https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS"

#: Versão do schema/aquisição da DFIN.
SOURCE_SCHEMA_VERSION = "cvm-dfin-v1"

_ALIASES: dict[str, tuple[str, ...]] = {
    "cnpj": ("CNPJ_Fundo_Classe", "CNPJ_Fundo"),
    "competencia": ("Data_Referencia", "DT_REFER", "DT_COMPTC"),
    "resultado": (
        "Lucro_Prejuizo",
        "Lucro_Liquido",
        "Resultado",
        "VL_LUCRO_PREJUIZO",
    ),
}

_OBRIGATORIAS = ("cnpj", "competencia", "resultado")

_ANOS_JANELA = 2


class CvmDfinRepository:
    """Fornece o resultado reportado da DFIN para reconciliação."""

    def __init__(
        self: "CvmDfinRepository",
        downloader: CvmDatasetDownloader | None = None,
    ) -> None:
        """Inicializa o repositório com o downloader informado ou um novo padrão."""
        self._downloader = downloader or CvmDatasetDownloader(
            base_url=CVM_DFIN_URL,
            arquivo=lambda ano: f"dfin_fii_{ano}.csv",
            dataset="FII-DFIN",
            parser_version=SOURCE_SCHEMA_VERSION,
            zipado=False,
        )

    def get_reported(
        self: "CvmDfinRepository", cnpj: str, reference_date: date
    ) -> Decimal | None:
        """Retorna o resultado reportado mais recente até a data de referência."""
        alvo = normalizar_cnpj(cnpj)
        if not alvo:
            return None
        melhor: tuple[date, Decimal] | None = None
        for ano in _anos(reference_date):
            data = self._carregar(ano)
            if data is None:
                continue
            for conteudo in self._downloader.extrair_csvs(data, ano).values():
                candidato = _buscar(conteudo, alvo, reference_date)
                if candidato is not None and (
                    melhor is None or candidato[0] > melhor[0]
                ):
                    melhor = candidato
        return melhor[1] if melhor else None

    def _carregar(self: "CvmDfinRepository", ano: int) -> bytes | None:
        """Carrega o arquivo anual, tolerando falhas de aquisição."""
        try:
            return self._downloader.baixar_ano(ano)
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao carregar DFIN de %s", ano, exc_info=True
            )
            return None


def _anos(reference_date: date) -> list[int]:
    """Retorna os anos a consultar, do mais recente para o mais antigo."""
    return sorted(
        {reference_date.year, reference_date.year - (_ANOS_JANELA - 1)},
        reverse=True,
    )


def _candidato_linha(
    bruta: dict[str, str],
    colunas: set[str],
    alvo: str,
    reference_date: date,
) -> tuple[date, Decimal] | None:
    """Avalia uma linha do CSV, retornando sua competência e resultado."""
    canonica = mapear_com_aliases(bruta, colunas, _ALIASES)
    if normalizar_cnpj(canonica.get("cnpj")) != alvo:
        return None
    competencia = parse_data(canonica.get("competencia"))
    valor = parse_decimal(canonica.get("resultado"))
    if competencia is None or valor is None or competencia > reference_date:
        return None
    return competencia, valor


def _buscar(
    conteudo: bytes, alvo: str, reference_date: date
) -> tuple[date, Decimal] | None:
    """Retorna a competência e o resultado do CNPJ mais recente no CSV."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return None
    colunas = {coluna.strip() for coluna in leitor.fieldnames}
    if not tem_alias(colunas, _ALIASES, "cnpj"):
        return None
    validar_aliases(colunas, _ALIASES, _OBRIGATORIAS)
    melhor: tuple[date, Decimal] | None = None
    for bruta in leitor:
        candidato = _candidato_linha(bruta, colunas, alvo, reference_date)
        if candidato is not None and (melhor is None or candidato[0] > melhor[0]):
            melhor = candidato
    return melhor
