"""Casos de uso da camada de aplicação para extração de proventos estruturados."""

import logging
from datetime import date, datetime, timedelta, timezone

from flowscope.application.structured_ports import (
    ProgressCallback,
    ProventosRepository,
    RegulacaoRepository,
)
from flowscope.domain.structured import (
    CategoriaMaterialFact,
    DocumentoProvento,
)

logger = logging.getLogger(__name__)

_TIPO_PROVENTOS = 41
_TIPO_FATOS = "fatos"
_TIPO_NOTICIAS = "noticias"
_TIPO_REGULACAO = "regulacao"


class ExtrairProventosUseCase:
    """Orquestra a extração de rendimentos e amortizações de um ticker."""

    def __init__(self: "ExtrairProventosUseCase", repository: ProventosRepository) -> None:
        """Inicializa o caso de uso com o repositório de proventos."""
        self._repository = repository

    def execute(
        self: "ExtrairProventosUseCase",
        ticker: str,
        data_inicio: date,
        data_fim: date,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DocumentoProvento]:
        """Extrai os proventos do ticker no período informado.

        Quando o ticker não resolve para um idFNET, retorna lista vazia sem
        erro. Falhas na extração de um documento individual são registradas
        como aviso e não interrompem o processamento dos demais documentos.
        """
        if progress_callback:
            progress_callback(f"Resolvendo ticker {ticker}", False)

        id_fnet = self._repository.resolver_ticker(ticker)
        if id_fnet is None:
            if progress_callback:
                progress_callback(f"Sem dados para {ticker}", False)
            return []

        if progress_callback:
            progress_callback(f"Listando documentos de {ticker}", False)

        documentos = self._repository.listar_documentos(
            id_fnet, data_inicio, data_fim, _TIPO_PROVENTOS
        )
        return self._extrair_documentos(
            documentos, ticker, id_fnet, progress_callback
        )

    def _extrair_documentos(
        self: "ExtrairProventosUseCase",
        documentos: list[dict],
        ticker: str,
        id_fnet: str,
        progress_callback: ProgressCallback | None,
    ) -> list[DocumentoProvento]:
        """Extrai os detalhes de cada documento, tolerando falhas individuais."""
        proventos: list[DocumentoProvento] = []
        for documento in documentos:
            contexto = dict(documento)
            contexto.setdefault("ticker", ticker)
            contexto.setdefault("id_fnet", id_fnet)
            id_documento = _id_do_documento(contexto)
            if not id_documento:
                continue
            try:
                if progress_callback:
                    progress_callback(f"Extraindo documento {id_documento}", False)
                proventos.append(self._repository.extrair_detalhes(contexto))
            except Exception as e:
                logger.warning(
                    "Erro ao extrair documento %s do ticker %s: %s",
                    id_documento,
                    ticker,
                    e,
                )
                if progress_callback:
                    progress_callback(f"Erro no documento {id_documento}", True)
        return proventos


def _id_do_documento(documento: dict) -> str:
    """Retorna o identificador do documento, da URL quando disponível."""
    id_documento = documento.get("idDocumento") or documento.get("id")
    if id_documento:
        return str(id_documento)
    return _id_da_url(str(documento.get("urlViewerFundosNet", "")))


def _id_da_url(url_documento: str) -> str:
    """Extrai o identificador do documento a partir da URL quando disponível."""
    from urllib.parse import parse_qs, urlparse

    if not url_documento:
        return ""
    consulta = parse_qs(urlparse(url_documento).query)
    if consulta.get("id"):
        return consulta["id"][0]
    return ""


class ExtrairDadosRegulatoriosUseCase:
    """Orquestra a extração de dados regulatórios e de mercado da B3."""

    def __init__(
        self: "ExtrairDadosRegulatoriosUseCase",
        repository: RegulacaoRepository,
    ) -> None:
        """Inicializa o caso de uso com o repositório de regulação."""
        self._repository = repository

    def execute(
        self: "ExtrairDadosRegulatoriosUseCase",
        tipo: str,
        ticker: str | None = None,
        categoria: CategoriaMaterialFact | str | None = None,
        agencia: str = "18",
        palavra: str | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> dict:
        """Extrai os dados regulatórios conforme o tipo solicitado."""
        if tipo == _TIPO_FATOS:
            return self._extrair_fatos(
                ticker=ticker,
                categoria=categoria,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        if tipo == _TIPO_NOTICIAS:
            return self._extrair_noticias(
                agencia=agencia,
                palavra=palavra,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        if tipo == _TIPO_REGULACAO:
            return self._extrair_regulacao()
        raise ValueError(f"Tipo de extração regulatória inválido: {tipo!r}")

    def _extrair_fatos(
        self: "ExtrairDadosRegulatoriosUseCase",
        *,
        ticker: str | None,
        categoria: CategoriaMaterialFact | str | None,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> dict:
        """Extrai fatos relevantes e assembleias do ticker, por categoria."""
        if ticker is None:
            raise ValueError("O ticker é obrigatório para extração de fatos relevantes")
        inicio, fim = _periodo_padrao(data_inicio, data_fim)
        code_cvm = self._repository.resolver_code_cvm(ticker)
        metadados = {"codeCVM": code_cvm, "empresa": None, "ticker": ticker}
        if code_cvm is None:
            return _resposta_fatos(metadados, [])
        codigos = _codigos_de_categoria(categoria)
        documentos: list[dict] = []
        for codigo in codigos:
            try:
                itens = self._repository.listar_fatos_relevantes(
                    code_cvm,
                    codigo,
                    inicio,
                    fim,
                    ticker=ticker,
                )
            except Exception as e:
                logger.warning(
                    "Erro ao listar categoria %s do ticker %s: %s",
                    codigo,
                    ticker,
                    e,
                )
                continue
            documentos.extend(item.to_dict() for item in itens)
        if documentos:
            metadados["empresa"] = documentos[0].get("companyName")
        return _resposta_fatos(metadados, documentos)

    def _extrair_noticias(
        self: "ExtrairDadosRegulatoriosUseCase",
        *,
        agencia: str,
        palavra: str | None,
        data_inicio: date | None,
        data_fim: date | None,
    ) -> dict:
        """Extrai as notícias do Plantão B3 no período informado."""
        noticias = self._repository.listar_noticias(
            agencia=agencia,
            palavra=palavra,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        return {
            "tipo": "noticias",
            "dataExtracao": datetime.now(timezone.utc).isoformat(),
            "noticias": [noticia.to_dict() for noticia in noticias],
        }

    def _extrair_regulacao(self: "ExtrairDadosRegulatoriosUseCase") -> dict:
        """Extrai censuras públicas e condições excepcionais da B3."""
        censuras = self._repository.listar_censuras()
        condicoes = self._repository.listar_condicoes_excepcionais()
        return {
            "tipo": "regulacao",
            "dataExtracao": datetime.now(timezone.utc).isoformat(),
            "censuras": [censura.to_dict() for censura in censuras],
            "condicoes": [condicao.to_dict() for condicao in condicoes],
        }


def _periodo_padrao(
    data_inicio: date | None, data_fim: date | None
) -> tuple[date, date]:
    """Retorna o período informado ou os últimos 30 dias como padrão."""
    fim = data_fim or datetime.now(timezone.utc).date()
    inicio = data_inicio or fim - timedelta(days=30)
    return inicio, fim


def _codigos_de_categoria(
    categoria: CategoriaMaterialFact | str | None,
) -> list[str]:
    """Valida e retorna os códigos de categoria a consultar."""
    if categoria is None:
        return [membro.value for membro in CategoriaMaterialFact]
    if isinstance(categoria, CategoriaMaterialFact):
        return [categoria.value]
    try:
        return [CategoriaMaterialFact(str(categoria)).value]
    except ValueError:
        raise ValueError(
            f"Categoria GetMaterialFacts inválida: {categoria!r}"
        ) from None


def _resposta_fatos(metadados: dict, documentos: list[dict]) -> dict:
    """Monta a resposta de fatos relevantes no formato da RFC-004."""
    return {
        "tipo": "fatos_relevantes",
        "dataExtracao": datetime.now(timezone.utc).isoformat(),
        "metadados": metadados,
        "documentos": documentos,
    }
