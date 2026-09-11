"""Aquisição do Informe Anual Estruturado da CVM (RFC-009).

Lê os arquivos ``geral`` e ``complemento`` do Informe Anual de FIIs, por CNPJ e
competência, e normaliza gestor, administrador, custodiante e auditor
independente. O arquivo anual bruto é cacheado com hash e versão do parser pelo
``CvmDatasetDownloader``.
"""

import csv
import io
import logging
from datetime import date

from flowscope.domain.cvm import AnnualReport, normalizar_cnpj
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader, parse_data

logger = logging.getLogger("flowscope")

#: Diretório oficial do Informe Anual Estruturado de FIIs.
CVM_ANNUAL_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/DADOS"

#: Versão do schema/aquisição do Informe Anual.
SOURCE_SCHEMA_VERSION = "cvm-inf-anual-v1"

#: Prefixos dos CSVs do Informe Anual usados na identidade fiscal.
_CSV_GERAL = "inf_anual_fii_geral"
_CSV_COMPLEMENTO = "inf_anual_fii_complemento"

#: Quantidade de anos consultados para trás a partir da referência.
_ANOS_JANELA = 2

#: Mapeamento coluna de origem → campo normalizado do administrador.
_CAMPOS_ADMINISTRADOR = {
    "nome_administrador": "Nome_Administrador",
    "cnpj_administrador": "CNPJ_Administrador",
}

#: Mapeamento coluna de origem → campo normalizado de gestor e prestadores.
_CAMPOS_GESTOR = {
    "nome_gestor": "Nome_Gestor",
    "cnpj_gestor": "CNPJ_Gestor",
    "nome_custodiante": "Nome_Custodiante",
    "cnpj_custodiante": "CNPJ_Custodiante",
    "nome_auditor": "Nome_Auditor_Independente",
    "cnpj_auditor": "CNPJ_Auditor_Independente",
}


class CvmAnnualRepository:
    """Fornece o registro mais recente do Informe Anual de um CNPJ."""

    def __init__(
        self: "CvmAnnualRepository",
        downloader: CvmDatasetDownloader | None = None,
    ) -> None:
        """Inicializa o repositório com o downloader informado ou um novo padrão."""
        self._downloader = downloader or CvmDatasetDownloader(
            base_url=CVM_ANNUAL_URL,
            arquivo=lambda ano: f"inf_anual_fii_{ano}.zip",
            dataset="FII-INF-ANUAL",
            parser_version=SOURCE_SCHEMA_VERSION,
        )

    def get(
        self: "CvmAnnualRepository",
        cnpj: str,
        reference_date: date,
        ticker: str = "",
    ) -> AnnualReport | None:
        """Retorna o registro mais recente do CNPJ até a data de referência."""
        alvo = normalizar_cnpj(cnpj)
        if not alvo:
            return None
        melhor: AnnualReport | None = None
        for ano in _anos(reference_date):
            csvs = self._carregar(ano)
            if not csvs:
                continue
            report = _registro_do_ano(csvs, alvo, reference_date)
            if report is None:
                continue
            if melhor is None or report.reference_date > melhor.reference_date:
                melhor = report
        if melhor is None:
            return None
        return AnnualReport(
            ticker=ticker.strip().upper(),
            cnpj_fundo_classe=melhor.cnpj_fundo_classe,
            reference_date=melhor.reference_date,
            nome_gestor=melhor.nome_gestor,
            cnpj_gestor=melhor.cnpj_gestor,
            nome_administrador=melhor.nome_administrador,
            cnpj_administrador=melhor.cnpj_administrador,
            nome_custodiante=melhor.nome_custodiante,
            cnpj_custodiante=melhor.cnpj_custodiante,
            nome_auditor=melhor.nome_auditor,
            cnpj_auditor=melhor.cnpj_auditor,
            source_file=melhor.source_file,
            source_hash=melhor.source_hash,
        )

    def _carregar(self: "CvmAnnualRepository", ano: int) -> dict[str, bytes]:
        """Carrega e extrai os CSVs do arquivo anual, tolerando falhas."""
        try:
            data = self._downloader.baixar_ano(ano)
            return self._downloader.extrair_csvs(data, ano)
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao carregar informe anual de %s", ano, exc_info=True
            )
            return {}


def _anos(reference_date: date) -> list[int]:
    """Retorna os anos a consultar, do mais recente para o mais antigo."""
    return [reference_date.year - i for i in range(_ANOS_JANELA)]


def _registro_do_ano(
    csvs: dict[str, bytes], alvo: str, reference_date: date
) -> AnnualReport | None:
    """Seleciona o registro mais recente do CNPJ nos CSVs anuais informados."""
    registros: dict[date, dict[str, str]] = {}
    for nome, conteudo in csvs.items():
        if _CSV_GERAL in nome:
            campos = _CAMPOS_ADMINISTRADOR
        elif _CSV_COMPLEMENTO in nome:
            campos = _CAMPOS_GESTOR
        else:
            continue
        for linha in _linhas(conteudo):
            if normalizar_cnpj(linha.get("CNPJ_Fundo_Classe")) != alvo:
                continue
            competencia = parse_data(linha.get("Data_Referencia"))
            if competencia is None or competencia > reference_date:
                continue
            atual = registros.setdefault(competencia, {})
            for chave, coluna in campos.items():
                valor = _texto(linha.get(coluna))
                if valor and not atual.get(chave):
                    atual[chave] = valor
    if not registros:
        return None
    competencia = max(registros)
    return AnnualReport(
        ticker="",
        cnpj_fundo_classe=alvo,
        reference_date=competencia,
        **registros[competencia],
    )


def _linhas(conteudo: bytes) -> list[dict[str, str]]:
    """Lê as linhas do CSV da CVM (latin1, delimitador ``;``)."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    return [linha for linha in leitor]


def _texto(valor: object) -> str | None:
    """Retorna o texto de um valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
