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
from decimal import Decimal, InvalidOperation

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
from flowscope.infrastructure.fii.parsing import moeda_para_decimal

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

#: Prefixo do CSV de complemento no ZIP do Informe Trimestral.
_CSV_COMPLEMENTO = "inf_trimestral_fii_complemento"

#: Colunas de identidade/controle que não representam componentes monetários.
_COLUNAS_NAO_MONETARIAS = frozenset(
    {
        "cnpj_fundo_classe",
        "cnpj_fundo",
        "data_referencia",
        "versao",
        "data_recebimento",
        "dt_comptc",
        "dt_receb",
        "dt_refer",
    }
)

#: Rótulo de exibição → coluna de percentual por indexador no complemento.
_INDEXADORES = {
    "IGP-M": "Percentual_Indexador_Valor_Total_IGPM",
    "INPC": "Percentual_Indexador_Valor_Total_INPC",
    "IPCA": "Percentual_Indexador_Valor_Total_IPCA",
    "INCC": "Percentual_Indexador_Valor_Total_INCC",
}


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
                if _CSV_COMPLEMENTO in nome:
                    continue
                for registro in _ler_registros(
                    conteudo, nome, alvo, reference_date
                ):
                    chave = (registro.competencia, registro.codigo)
                    atual = selecionados.get(chave)
                    if atual is None or registro.versao > atual.versao:
                        selecionados[chave] = registro
        return [_para_componente(registro, alvo) for registro in selecionados.values()]

    def get_indexadores(
        self: "CvmQuarterlyRepository",
        cnpj: str,
        reference_date: date,
    ) -> dict[str, Decimal]:
        """Retorna o percentual por indexador do complemento mais recente.

        Considera apenas os indexadores com percentual positivo; ausência de
        registro ou de valores resulta em dicionário vazio.
        """
        alvo = normalizar_cnpj(cnpj)
        if not alvo:
            return {}
        melhor: tuple[date, dict[str, Decimal]] | None = None
        for ano in _anos(reference_date):
            data = self._carregar(ano)
            if data is None:
                continue
            for nome, conteudo in self._downloader.extrair_csvs(data, ano).items():
                if _CSV_COMPLEMENTO not in nome:
                    continue
                for competencia, valores in _ler_indexadores(
                    conteudo, alvo, reference_date
                ):
                    if melhor is None or competencia > melhor[0]:
                        melhor = (competencia, valores)
        return melhor[1] if melhor is not None else {}

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


def _ler_indexadores(
    conteudo: bytes, alvo: str, reference_date: date
) -> list[tuple[date, dict[str, Decimal]]]:
    """Lê os percentuais por indexador do CSV de complemento."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    resultado: list[tuple[date, dict[str, Decimal]]] = []
    for linha in leitor:
        if normalizar_cnpj(linha.get("CNPJ_Fundo_Classe")) != alvo:
            continue
        competencia = parse_data(linha.get("Data_Referencia"))
        if competencia is None or competencia > reference_date:
            continue
        valores = {
            rotulo: valor
            for rotulo, coluna in _INDEXADORES.items()
            if (valor := _decimal_cvm(linha.get(coluna))) is not None
            and valor > Decimal(0)
        }
        if valores:
            resultado.append((competencia, valores))
    return resultado


def _decimal_cvm(valor: object) -> Decimal | None:
    """Interpreta um percentual da CVM com ponto ou vírgula decimal."""
    if valor is None:
        return None
    texto = str(valor).strip().replace(" ", "")
    if not texto:
        return None
    try:
        if "," in texto:
            return moeda_para_decimal(texto)
        return Decimal(texto)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _registro_linha(
    bruta: dict[str, str],
    colunas: set[str],
    alvo: str,
    reference_date: date,
    arquivo: str,
) -> _Registro | None:
    """Normaliza uma linha do CSV em ``_Registro``, ou ``None`` se descartável."""
    canonica = mapear_com_aliases(bruta, colunas, _ALIASES)
    if normalizar_cnpj(canonica.get("cnpj")) != alvo:
        return None
    competencia = parse_data(canonica.get("competencia"))
    if competencia is None or competencia > reference_date:
        return None
    valor = parse_decimal(canonica.get("valor"))
    if valor is None:
        return None
    return _Registro(
        competencia=competencia,
        codigo=str(canonica.get("codigo") or ""),
        descricao=str(canonica.get("descricao") or ""),
        valor=valor,
        versao=parse_inteiro(canonica.get("versao")),
        arquivo=arquivo,
    )


def _ler_registros(
    conteudo: bytes,
    arquivo: str,
    alvo: str,
    reference_date: date,
) -> list[_Registro]:
    """Lê os componentes do CNPJ no CSV, preservando o código original.

    Aceita dois layouts: o longo legado (``Descricao``/``Valor``) e o largo de
    resultado contábil-financeiro (uma coluna monetária por componente).
    """
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    colunas = {coluna.strip() for coluna in leitor.fieldnames}
    if not tem_alias(colunas, _ALIASES, "cnpj"):
        return []
    if tem_alias(colunas, _ALIASES, "descricao") and tem_alias(
        colunas, _ALIASES, "valor"
    ):
        validar_aliases(colunas, _ALIASES, _OBRIGATORIAS)
        return _ler_layout_longo(
            leitor, colunas, alvo, reference_date, arquivo
        )
    if _tem_coluna_monetaria(leitor.fieldnames) and tem_alias(
        colunas, _ALIASES, "competencia"
    ):
        return _ler_layout_largo(
            leitor, colunas, alvo, reference_date, arquivo
        )
    validar_aliases(colunas, _ALIASES, _OBRIGATORIAS)
    return []


def _tem_coluna_monetaria(fieldnames: object) -> bool:
    """Indica se o CSV possui alguma coluna que não seja de identidade."""
    return bool(_colunas_monetarias(fieldnames))


def _colunas_monetarias(fieldnames: object) -> list[str]:
    """Retorna os nomes das colunas que representam valores monetários."""
    return [
        str(coluna)
        for coluna in fieldnames
        if str(coluna).strip().lower() not in _COLUNAS_NAO_MONETARIAS
    ]


def _ler_layout_longo(
    leitor: "csv.DictReader",
    colunas: set[str],
    alvo: str,
    reference_date: date,
    arquivo: str,
) -> list[_Registro]:
    """Lê o layout longo legado (``Descricao``/``Valor``)."""
    registros: list[_Registro] = []
    for bruta in leitor:
        registro = _registro_linha(
            bruta, colunas, alvo, reference_date, arquivo
        )
        if registro is not None:
            registros.append(registro)
    return registros


def _registro_do_valor(
    coluna: str,
    valor: Decimal,
    competencia: date,
    versao: int | None,
    arquivo: str,
) -> _Registro:
    """Monta um registro de componente a partir de uma coluna monetária."""
    codigo = coluna.strip()
    return _Registro(
        competencia=competencia,
        codigo=codigo,
        descricao=codigo.replace("_", " ").strip(),
        valor=valor,
        versao=versao,
        arquivo=arquivo,
    )


def _ler_layout_largo(
    leitor: "csv.DictReader",
    colunas: set[str],
    alvo: str,
    reference_date: date,
    arquivo: str,
) -> list[_Registro]:
    """Lê o layout largo, convertendo cada coluna monetária em componente."""
    monetarias = _colunas_monetarias(leitor.fieldnames or [])
    registros: list[_Registro] = []
    for bruta in leitor:
        canonica = mapear_com_aliases(bruta, colunas, _ALIASES)
        if normalizar_cnpj(canonica.get("cnpj")) != alvo:
            continue
        competencia = parse_data(canonica.get("competencia"))
        if competencia is None or competencia > reference_date:
            continue
        versao = parse_inteiro(canonica.get("versao"))
        for coluna in monetarias:
            valor = parse_decimal(bruta.get(coluna))
            if valor is None or valor == Decimal(0):
                continue
            registros.append(
                _registro_do_valor(
                    coluna, valor, competencia, versao, arquivo
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
