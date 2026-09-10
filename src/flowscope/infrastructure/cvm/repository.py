"""Repositório do Informe Mensal Estruturado da CVM (RFC-009 §19-25)."""

import csv
import io
import logging
from datetime import date

from flowscope.domain.cvm import MonthlyReport, normalizar_cnpj
from flowscope.infrastructure.cvm.downloader import (
    CvmMonthlyDownloader,
    hash_sha256,
)
from flowscope.infrastructure.cvm.schema import (
    mapear_linha,
    tem_coluna_identidade,
    validar_schema,
)

logger = logging.getLogger("flowscope")

#: Quantidade de anos consultados para trás a partir da referência.
_ANOS_JANELA = 2


class CvmMonthlyReportRepository:
    """Localiza o registro do Informe Mensal de um CNPJ por competência."""

    def __init__(
        self: "CvmMonthlyReportRepository",
        downloader: CvmMonthlyDownloader | None = None,
    ) -> None:
        """Inicializa o repositório com o downloader informado ou um novo padrão."""
        self._downloader = downloader or CvmMonthlyDownloader()

    def get(
        self: "CvmMonthlyReportRepository",
        cnpj: str,
        reference_date: date,
        ticker: str = "",
    ) -> MonthlyReport | None:
        """Retorna o registro mais recente do CNPJ até a data de referência."""
        alvo = normalizar_cnpj(cnpj)
        if not alvo:
            return None
        melhor: MonthlyReport | None = None
        for ano in self._anos(reference_date):
            data = self._carregar_ano(ano)
            if data is None:
                continue
            digest = hash_sha256(data)
            for nome, conteudo in self._downloader.extrair_csvs(data).items():
                for report in self._reports_do_csv(
                    conteudo, nome, digest, alvo, reference_date, ticker
                ):
                    if melhor is None or _mais_recente(report, melhor):
                        melhor = report
        return melhor

    def get_by_ticker(
        self: "CvmMonthlyReportRepository",
        ticker: str,
        reference_date: date,
        identity: object | None = None,
    ) -> MonthlyReport | None:
        """Resolve a identidade do ticker e retorna o seu Informe Mensal."""
        from flowscope.infrastructure.cvm.identity import resolver_identidade

        identidade = identity or resolver_identidade(ticker)
        if identidade is None:
            return None
        return self.get(
            identidade.cnpj_fundo_classe, reference_date, ticker=ticker
        )

    def _anos(self: "CvmMonthlyReportRepository", reference_date: date) -> list[int]:
        """Retorna os anos a consultar, do mais recente para o mais antigo."""
        return sorted(
            {reference_date.year, reference_date.year - (_ANOS_JANELA - 1)},
            reverse=True,
        )

    def _carregar_ano(
        self: "CvmMonthlyReportRepository", ano: int
    ) -> bytes | None:
        """Carrega o ZIP anual, tolerando falhas de aquisição."""
        try:
            return self._downloader.baixar_ano(ano)
        except Exception:  # aquisição tolerante
            logger.warning(
                "Falha ao carregar informe CVM de %s", ano, exc_info=True
            )
            return None

    def _reports_do_csv(
        self: "CvmMonthlyReportRepository",
        conteudo: bytes,
        nome: str,
        digest: str,
        alvo: str,
        reference_date: date,
        ticker: str,
    ) -> list[MonthlyReport]:
        """Extrai os registros do CNPJ no CSV que correspondem à competência."""
        reports: list[MonthlyReport] = []
        for linha in _ler_linhas(conteudo):
            if normalizar_cnpj(linha.get("cnpj")) != alvo:
                continue
            competencia = _parse_data(linha.get("competencia"))
            if competencia is None or competencia > reference_date:
                continue
            reports.append(
                MonthlyReport(
                    ticker=ticker.strip().upper(),
                    cnpj_fundo_classe=alvo,
                    reference_date=competencia,
                    raw_rows=linha,
                    source_file=nome,
                    source_hash=digest,
                    is_latest=True,
                    source_version=_texto(linha.get("versao")),
                    received_at=_texto(linha.get("recebimento")),
                )
            )
        return reports


def _ler_linhas(conteudo: bytes) -> list[dict]:
    """Lê as linhas do CSV mapeadas para o schema canônico."""
    texto = conteudo.decode("latin1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    if leitor.fieldnames is None:
        return []
    colunas = {coluna.strip() for coluna in leitor.fieldnames}
    if not tem_coluna_identidade(colunas):
        return []
    validar_schema(colunas)
    linhas: list[dict] = []
    for bruta in leitor:
        if not any(bruta.values()):
            continue
        linha = mapear_linha(bruta, colunas)
        if linha.get("cnpj"):
            linhas.append(linha)
    return linhas


def _mais_recente(candidato: MonthlyReport, atual: MonthlyReport) -> bool:
    """Indica se o candidato é mais recente que o registro atual."""
    if candidato.reference_date != atual.reference_date:
        return candidato.reference_date > atual.reference_date
    return _ordem_versao(candidato) > _ordem_versao(atual)


def _ordem_versao(report: MonthlyReport) -> tuple[int, str]:
    """Chave de ordenação por versão e data de recebimento."""
    return (_inteiro(report.source_version), report.received_at or "")


def _inteiro(valor: object) -> int:
    """Interpreta um valor como inteiro, retornando zero quando inválido."""
    try:
        return int(str(valor))
    except (TypeError, ValueError):
        return 0


def _texto(valor: object) -> str | None:
    """Retorna o texto de um valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _parse_data(valor: object) -> date | None:
    """Interpreta uma data ISO (``AAAA-MM-DD``) ou brasileira (``DD/MM/AAAA``)."""
    if not valor:
        return None
    texto = str(valor).strip()[:10]
    if "-" in texto:
        partes = texto.split("-")
        ano, mes, dia = partes[0], partes[1], partes[2]
    elif "/" in texto:
        partes = texto.split("/")
        dia, mes, ano = partes[0], partes[1], partes[2]
    else:
        return None
    try:
        return date(int(ano), int(mes), int(dia))
    except ValueError:
        return None
