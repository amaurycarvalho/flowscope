"""Cliente HTTP para a API de fundos listados da B3 (fundsListedProxy)."""

import base64
import json
import logging
from datetime import date

import requests

from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger(__name__)

_BASE_URL = "https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search"
_TIPO_PROVENTOS = 41
_PAGE_SIZE = 20


class B3FundosClient:
    """Consulta a API de fundos listados da B3 com cache local.

    Responsável pela resolução de tickers para ``idFNET``, listagem paginada
    de relatórios estruturados e download do HTML dos documentos.
    """

    _BASE_URL = _BASE_URL

    def __init__(self: "B3FundosClient", cache: CacheManager | None = None) -> None:
        """Inicializa o cliente com o gerenciador de cache informado ou um novo padrão."""
        self._cache = cache or CacheManager()

    def _build_token(self: "B3FundosClient", payload: dict[str, object]) -> str:
        """Serializa o payload em JSON compacto e codifica em Base64."""
        raw = json.dumps(payload, separators=(",", ":"))
        return base64.b64encode(raw.encode()).decode()

    def _get_json(self: "B3FundosClient", endpoint: str, payload: dict[str, object]) -> object:
        """Executa o GET do endpoint informado com o token construído do payload."""
        token = self._build_token(payload)
        url = f"{_BASE_URL}/{endpoint}/{token}"
        logger.info("Consultando %s", url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def resolver_ticker(
        self: "B3FundosClient",
        ticker: str,
        type_fund: str = "FII",
    ) -> str | None:
        """Resolve o ticker para o ``idFNET`` na B3.

        Retorna ``None`` para tickers sem dados na API de fundos, sem lançar
        exceção. O resultado, inclusive ``None``, é cacheado por 30 dias.
        """
        id_cem = _fund_root(ticker)

        def _fetch() -> dict[str, object]:
            try:
                dados = self._get_json(
                    "GetListClassFund",
                    {
                        "language": "pt-br",
                        "idCEM": id_cem,
                        "typeFund": type_fund,
                    },
                )
            except requests.RequestException as e:
                logger.warning("Falha ao resolver ticker %s: %s", ticker, e)
                return {"idFNET": None}
            if not isinstance(dados, list):
                return {"idFNET": None}
            for item in dados:
                if not isinstance(item, dict):
                    continue
                if "Fundo:" in str(item.get("tradingName", "")):
                    continue
                id_fnet = item.get("id")
                if id_fnet:
                    return {"idFNET": str(id_fnet)}
            return {"idFNET": None}

        key = f"fund_resolution_{ticker.upper()}"
        try:
            payload = self._cache.get_or_fetch(key, ttl_days=30, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao resolver ticker %s", ticker, exc_info=True)
            return None
        return payload.get("idFNET")

    def listar_documentos(
        self: "B3FundosClient",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int = _TIPO_PROVENTOS,
        type_fund: str = "FII",
    ) -> list[dict]:
        """Lista os relatórios estruturados do tipo informado, paginando quando necessário."""
        documentos: list[dict] = []
        page_number = 1
        while True:
            pagina = self._listar_pagina(
                id_fnet, data_inicio, data_fim, tipo, type_fund, page_number
            )
            resultados = pagina.get("results", [])
            if isinstance(resultados, list):
                documentos.extend(resultados)
            total_pages = int(pagina.get("page", {}).get("totalPages", 1) or 1)
            if page_number >= total_pages:
                break
            page_number += 1
        return documentos

    def _listar_pagina(
        self: "B3FundosClient",
        id_fnet: str,
        data_inicio: date,
        data_fim: date,
        tipo: int,
        type_fund: str,
        page_number: int,
    ) -> dict[str, object]:
        """Busca uma página da listagem de relatórios, com cache de 1 dia."""
        key = (
            f"fund_docs_{id_fnet}_{tipo}_{data_inicio.isoformat()}_"
            f"{data_fim.isoformat()}_{page_number}"
        )

        def _fetch() -> dict[str, object]:
            return self._get_json(
                "GetStructuredReports",
                {
                    "language": "pt-br",
                    "dataInicial": data_inicio.isoformat(),
                    "dataFinal": data_fim.isoformat(),
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                    "idFNET": id_fnet,
                    "typeFund": type_fund,
                    "type": tipo,
                },
            )

        try:
            return self._cache.get_or_fetch(key, ttl_days=1, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao listar documentos do idFNET %s (página %d)",
                id_fnet,
                page_number,
                exc_info=True,
            )
            return {"results": [], "page": {"totalPages": 1, "totalRecords": 0}}

    def buscar_html_documento(self: "B3FundosClient", id_documento: str) -> str:
        """Baixa e retorna o HTML do documento de provento informado."""
        url = (
            "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento"
            f"?id={id_documento}"
        )
        logger.info("Baixando documento %s via %s", id_documento, url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text


def _fund_root(ticker: str) -> str:
    """Remove o sufixo ``11`` do ticker, devolvendo o código do fundo."""
    ticker = ticker.strip().upper()
    if ticker.endswith("11"):
        return ticker[:-2]
    return ticker
