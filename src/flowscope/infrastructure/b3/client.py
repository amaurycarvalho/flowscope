from datetime import date
from typing import Any

from flowscope.infrastructure.cache import CacheManager


class B3Client:
    _BASE_URL = "https://sistemaswebb3-listados.b3.com.br"

    def __init__(self, cache: CacheManager | None = None):
        self._cache = cache or CacheManager()

    def _request_token(self, file_name: str, ref_date: date) -> dict[str, Any]:
        import requests

        url = f"{self._BASE_URL}/api/download/requestname"
        payload = {
            "fileName": file_name,
            "date": ref_date.strftime("%Y-%m-%d"),
        }
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _download_csv(self, token: str) -> str:
        import requests

        url = f"{self._BASE_URL}/api/download/"
        resp = requests.get(url, params={"token": token}, timeout=60)
        resp.raise_for_status()
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
