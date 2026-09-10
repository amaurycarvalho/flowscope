"""Aquisição do Informe Trimestral Estruturado da CVM (RFC-010 §9).

Lê os componentes de resultado por CNPJ e competência, preserva o código
original de cada linha, trata reapresentações e os normaliza em
``FFOComponent`` com proveniência.
"""

import csv
import io
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from flowscope.domain.cvm import normalizar_cnpj
from flowscope.domain.ffo import (
    ComponentProvenance,
    FFOComponent,
    classificar_componente,
)
from flowscope.infrastructure.cvm.datasets import (
    CvmDatasetDownloader,
    parse_data,
    parse_decimal,
    parse_inteiro,
)
from flowscope.infrastructure.cvm.schema import (
    mapear_com_aliases,
    tem_alias,
    validar_aliases,
)

logger = logging.getLogger("flowscope")

#: Diretório oficial do Informe Trimestral Estruturado de FIIs.
CVM_QUARTERLY_URL = (
    "https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS"
)

#: Versão do schema/aquisição do Informe Trimestral.
SOURCE_SCHEMA_VERSION = "cvm-inf-trimestral-v1"

_ALIASES: dict[str, tuple[str, ...]] = {
    "cnpj": ("CNPJ_Fundo_Classe", "CNPJ_Fundo"),
    "competencia": ("Data_Referencia", "DT_COMPTC", "DT_REFER"),
    "descricao": ("Descricao", "Descricao_Conta", "DS_CONTA", "Conta"),
    "valor": ("Valor", "VL_CONTA", "Valor_Conta"),
    "codigo": ("Codigo", "Codigo_Conta", "CD_CONTA"),
    "versao": ("Versao", "VERSAO"),
    "recebimento": ("Data_Recebimento", "DT_RECEB"),
}

_OBRIGATORIAS = ("cnpj", "competencia", "descricao", "valor")

_ANOS_JANELA = 2


@dataclass(frozen=True)
class _Registro:
    """Linha de componente normalizada antes da classificação."""

    competencia: date
    codigo: str
    descricao: str
    valor: Decimal
    versao: int
    arquivo: str


class CvmQuarterlyRepository:
    """Fornece os componentes de resultado do Informe Trimestral."""

    def __init__(
        self: "CvmQuarterlyRepository",
        downloader: CvmDatasetDownloader | None = None,
    ) -> None:
        """Inicializa o repositório com o downloader informado ou um novo padrão."""
        self._downloader = downloader or CvmDatasetDownloader(
            base_url=CVM_QUARTERLY_URL,
            arquivo=lambda ano: f"inf_trimestral_fii_{ano}.zip",
            dataset="FII-INF-TRIMESTRAL",
            parser_version=SOURCE_SCHEMA_VERSION,
        )

    def get_components(
        self: "CvmQuarterlyRepository",
        cnpj: str,
        reference_date: date,
        ticker: str = "",
    ) -> list[FFOComponent]:
        """Retorna os componentes do CNPJ até a data de referência."""
        alvo = normalizar_cnpj(cnpj)
        if not alvo:
            return []
        selecionados: dict[tuple[date, str], _Registro] = {}
        for ano in _anos(reference_date):
            data = self._carregar(ano)
            if data is None:
                continue
            for nome, conteudo in self._downloader.extrair_csvs(data, ano).items():
                for registro in _ler_registros(
                    conteudo, nome, alvo, reference_date
                ):
                    chave = (registro.competencia, registro.codigo)
                    atual = selecionados.get(chave)
                    if atual is None or registro.versao > atual.versao:
                        selecionados[chave] = registro
        return [_para_componente(registro, alvo) for registro in selecionados.values()]

    def _carregar(self: "CvmQuarterlyRepository", ano: int) -> bytes | None:
        """Carrega o arquivo anual, tolerando falhas de aquisição."""
        try:
            return self._downloader.baixar_ano(ano)
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao carregar informe trimestral de %s", ano, exc_info=True
            )
            return None


def _anos(reference_date: date) -> list[int]:
    """Retorna os anos a consultar, do mais recente para o mais antigo."""
    return sorted(
        {reference_date.year, reference_date.year - (_ANOS_JANELA - 1)},
        reverse=True,
    )


def _ler_registros(
    conteudo: bytes,
    arquivo: str,
    alvo: str,
    reference_date: date,
) -> list[_Registro]:
    """Lê os componentes do CNPJ no CSV, preservando o código original."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    colunas = {coluna.strip() for coluna in leitor.fieldnames}
    if not tem_alias(colunas, _ALIASES, "cnpj"):
        return []
    validar_aliases(colunas, _ALIASES, _OBRIGATORIAS)
    registros: list[_Registro] = []
    for bruta in leitor:
        canonica = mapear_com_aliases(bruta, colunas, _ALIASES)
        if normalizar_cnpj(canonica.get("cnpj")) != alvo:
            continue
        competencia = parse_data(canonica.get("competencia"))
        if competencia is None or competencia > reference_date:
            continue
        valor = parse_decimal(canonica.get("valor"))
        if valor is None:
            continue
        registros.append(
            _Registro(
                competencia=competencia,
                codigo=str(canonica.get("codigo") or ""),
                descricao=str(canonica.get("descricao") or ""),
                valor=valor,
                versao=parse_inteiro(canonica.get("versao")),
                arquivo=arquivo,
            )
        )
    return registros


def _para_componente(registro: _Registro, cnpj: str) -> FFOComponent:
    """Monta o componente de domínio com classificação e proveniência."""
    return FFOComponent(
        description=registro.descricao,
        value=registro.valor,
        classification=classificar_componente(registro.descricao),
        provenance=ComponentProvenance(
            source="CVM",
            dataset="INF_TRIMESTRAL",
            file=registro.arquivo,
            cnpj=cnpj,
            reference_date=registro.competencia,
            field=registro.codigo or registro.descricao,
        ),
        code=registro.codigo,
    )
