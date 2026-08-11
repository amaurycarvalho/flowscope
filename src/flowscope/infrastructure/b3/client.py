"""Cliente HTTP para baixar arquivos de negociação e carteiras da B3."""

import base64
import json
import logging
from collections.abc import Callable
from datetime import date
from typing import Any

from flowscope.infrastructure.b3.parser import parse_index_csv
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger(__name__)


class B3Client:
    """Baixa e armazena em cache arquivos de negociação e carteiras da B3."""

    _BASE_URL = "https://arquivos.b3.com.br"
    _BASE_PORTFOLIO_URL = (
        "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/"
        "GetDownloadPortfolioDay/"
    )

    def __init__(self: "B3Client", cache: CacheManager | None = None) -> None:
        """Inicializa o cliente com o gerenciador de cache informado ou um novo padrão."""
        self._cache = cache or CacheManager()
        self._bust_stale_portfolio_cache()

    def _bust_stale_portfolio_cache(self: "B3Client") -> None:
        for index in ("IBOV", "IDIV", "IFIX"):
            key = f"portfolio_{index}"
            meta_path = self._cache._cache_dir / f"{key}.json"
            if meta_path.exists():
                try:
                    data = json.loads(meta_path.read_text(encoding="utf-8"))
                    tickers = data.get("tickers", [])
                    if not tickers:
                        logger.info("Busting stale empty cache for %s", key)
                        meta_path.unlink()
                except (json.JSONDecodeError, KeyError, OSError):
                    pass

    def _request_token(self: "B3Client", file_name: str, ref_date: date) -> dict[str, Any]:
        import requests

        url = f"{self._BASE_URL}/api/download/requestname"
        params = {
            "fileName": file_name,
            "date": ref_date.strftime("%Y-%m-%d"),
        }
        resp = requests.get(url, params=params, timeout=30)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Erro HTTP {resp.status_code} ao obter token para {file_name} em {ref_date}"
            ) from e
        return resp.json()

    def _download_csv(self: "B3Client", token: str) -> str:
        import requests

        url = f"{self._BASE_URL}/api/download/"
        resp = requests.get(url, params={"token": token}, timeout=60)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Erro HTTP {resp.status_code} ao baixar CSV"
            ) from e
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text

    def fetch_file(self: "B3Client", date_key: date, file_name: str = "TradeInformationConsolidated",
                   progress_callback: Callable[[str, bool], None] | None = None,
                   cache_only: bool = False) -> str | None:
        """Baixa o arquivo de negociação da data, usando o cache quando disponível."""
        cached = self._cache.get(date_key)
        if cached is not None:
            if progress_callback:
                progress_callback(f"{date_key} (em cache)", False)
            return cached
        if cache_only:
            if progress_callback:
                progress_callback(f"{date_key} (sem cache)", True)
            return None
        token_data = self._request_token(file_name, date_key)
        token = token_data.get("token") or token_data.get("redirectUrl", "")
        content = self._download_csv(token)
        self._cache.put(date_key, content)
        if progress_callback:
            progress_callback(str(date_key), False)
        return content

    def _build_portfolio_url(self: "B3Client", index: str, language: str = "pt-br") -> str:
        payload = json.dumps({"index": index, "language": language}, separators=(",", ":"))
        b64 = base64.b64encode(payload.encode()).decode()
        return f"{self._BASE_PORTFOLIO_URL}{b64}"

    def fetch_portfolio(self: "B3Client", index: str, language: str = "pt-br",
                        progress_callback: Callable[[str, bool], None] | None = None) -> list[str]:
        """Baixa e retorna a lista de tickers do índice, usando o cache com validade de 7 dias."""
        def _fetch() -> dict[str, object]:
            import requests

            url = self._build_portfolio_url(index, language)
            logger.info("Fetching portfolio %s via %s", index, url)
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            raw = resp.text.strip()
            logger.info("Response for %s: %d bytes", index, len(raw))
            if not raw:
                raise RuntimeError(f"Empty response for portfolio {index}")
            try:
                decoded = base64.b64decode(raw).decode("latin-1")
            except (ValueError, TypeError):
                decoded = raw
            tickers = parse_index_csv(decoded)
            logger.info("Parsed %d tickers from %s", len(tickers), index)
            if not tickers:
                raise RuntimeError(f"No tickers parsed for {index}")
            return {"tickers": tickers, "index": index}

        try:
            key = f"portfolio_{index}"
            data = self._cache.get_or_fetch(key, ttl_days=7, fetch_fn=_fetch)
            result = data["tickers"]
            if not result:
                self._cache.invalidate(key)
                raise RuntimeError(f"Cached empty result for {index}")
            if progress_callback:
                progress_callback(f"Portfólio {index}: {len(result)} ativos", False)
            return result
        except Exception:
            logger.exception("Failed to fetch portfolio %s", index)
            if progress_callback:
                progress_callback(f"Falha ao baixar portfólio {index}", True)
            return []
