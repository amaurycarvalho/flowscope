import base64
from datetime import date
from typing import Any

from flowscope.infrastructure.b3.parser import parse_idiv_csv
from flowscope.infrastructure.cache import CacheManager


class B3Client:
    _BASE_URL = "https://arquivos.b3.com.br"
    _IDIV_URL = (
        "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/"
        "GetDownloadPortfolioDay/"
        "eyJpbmRleCI6IklESVYiLCJsYW5ndWFnZSI6InB0LWJyIn0="
    )

    def __init__(self, cache: CacheManager | None = None):
        self._cache = cache or CacheManager()

    def _request_token(self, file_name: str, ref_date: date) -> dict[str, Any]:
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

    def _download_csv(self, token: str) -> str:
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

    def fetch_file(self, date_key: date, file_name: str = "TradeInformationConsolidated") -> str:
        cached = self._cache.get(date_key)
        if cached is not None:
            return cached
        token_data = self._request_token(file_name, date_key)
        token = token_data.get("token") or token_data.get("redirectUrl", "")
        content = self._download_csv(token)
        self._cache.put(date_key, content)
        return content

    def fetch_idiv_portfolio(self) -> list[str]:
        def _fetch():
            import requests

            resp = requests.get(self._IDIV_URL, timeout=30)
            resp.raise_for_status()
            raw = resp.text.strip()
            try:
                decoded = base64.b64decode(raw).decode("latin-1")
            except Exception:
                decoded = raw
            tickers = parse_idiv_csv(decoded)
            return {"tickers": tickers}

        try:
            data = self._cache.get_or_fetch("idiv_portfolio_v2", ttl_days=7, fetch_fn=_fetch)
            return data["tickers"]
        except Exception:
            return []
