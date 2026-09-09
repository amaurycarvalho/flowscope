"""Repositório de proventos que combina o cliente de fundos e o parsing HTML."""

from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

from flowscope.application.structured_ports import ProventosRepository
from flowscope.domain.structured import DocumentoProvento
from flowscope.infrastructure.b3.funds_client import B3FundosClient
from flowscope.infrastructure.b3.structured_extractor import extrair_documento_provento


class FundosRepository(ProventosRepository):
    """Implementa o port ``ProventosRepository`` usando o ``B3FundosClient``."""

    def __init__(self: "FundosRepository", client: B3FundosClient | None = None) -> None:
        """Inicializa o repositório com o cliente de fundos informado ou um novo padrão."""
        self._client = client or B3FundosClient()

    def resolver_ticker(self: "FundosRepository", ticker: str) -> str | None:
        """Resolve o ticker para o ``idFNET``, delegando ao cliente de fundos."""
        return self._client.resolver_ticker(ticker)

    def listar_documentos(
        self: "FundosRepository",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int,
    ) -> list[dict]:
        """Lista os documentos do idFNET no período informado, delegando ao cliente."""
        return self._client.listar_documentos(id_fnet, data_inicio, data_fim, tipo)

    def extrair_detalhes(self: "FundosRepository", documento: dict) -> DocumentoProvento:
        """Baixa e extrai os detalhes de um documento de provento listado."""
        url_documento = str(documento.get("urlViewerFundosNet") or "")
        id_documento = _id_do_documento(documento, url_documento)
        html = self._client.buscar_html_documento(id_documento)
        ticker = documento.get("ticker", "")
        id_fnet = documento.get("id_fnet", "") or documento.get("idFNET", "")
        extraido = extrair_documento_provento(
            html,
            id_documento=id_documento,
            url_documento=url_documento,
            data_extracao=datetime.now(timezone.utc).isoformat(),
            ticker=str(ticker or ""),
            id_fnet=str(id_fnet or ""),
        )
        if extraido is None:
            raise ValueError(f"Nenhum provento encontrado no documento {id_documento}")
        return extraido


def _id_do_documento(documento: dict, url_documento: str) -> str:
    """Extrai o identificador do documento a partir da URL ou do dicionário."""
    if url_documento:
        consulta = parse_qs(urlparse(url_documento).query)
        if consulta.get("id"):
            return consulta["id"][0]
        partes = [p for p in url_documento.rstrip("/").split("/") if p]
        if partes:
            ultima = partes[-1]
            if ultima.isdigit():
                return ultima
    for chave in ("idDocumento", "id_documento", "id"):
        if documento.get(chave):
            return str(documento[chave])
    raise ValueError(f"Documento sem identificador: {url_documento!r}")
