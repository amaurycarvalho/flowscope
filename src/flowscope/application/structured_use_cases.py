"""Casos de uso da camada de aplicação para extração de proventos estruturados."""

import logging
from datetime import date

from flowscope.application.structured_ports import (
    ProgressCallback,
    ProventosRepository,
)
from flowscope.domain.structured import DocumentoProvento

logger = logging.getLogger(__name__)

_TIPO_PROVENTOS = 41


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
