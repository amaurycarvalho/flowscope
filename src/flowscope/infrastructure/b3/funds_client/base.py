"""Cliente base: sessão HTTP, serialização e retry."""

import logging
from collections.abc import Callable

import requests

from flowscope.infrastructure.b3.encoder import encode_b3_payload
from flowscope.infrastructure.b3.funds_client.constants import (
    _BASE_URL,
    _LISTED_BASE_URL,
)
from flowscope.infrastructure.b3.rate_limit import SerializadorPorHost
from flowscope.infrastructure.b3.retry import RETRY_DELAYS, executar_com_retry
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger(__name__)


class _FundosBase:
    """Primitivas HTTP compartilhadas pelos mixins de aquisição da B3."""

    _BASE_URL = _BASE_URL

    def __init__(
        self: "_FundosBase",
        cache: CacheManager | None = None,
        session: requests.Session | None = None,
        serializador: SerializadorPorHost | None = None,
        retry_delays: tuple[float, ...] = RETRY_DELAYS,
    ) -> None:
        """Inicializa o cliente com cache, sessão HTTP e serializador por host."""
        self._cache = cache or CacheManager()
        self._session = session or requests.Session()
        self._serializador = serializador or SerializadorPorHost()
        self._retry_delays = tuple(retry_delays)

    def _build_token(self: "_FundosBase", payload: dict[str, object]) -> str:
        """Serializa o payload em JSON compacto e codifica em Base64."""
        return encode_b3_payload(payload)

    def _requisicao_get(
        self: "_FundosBase", url: str, timeout: int = 30, **kwargs: object
    ) -> requests.Response:
        """Executa um GET serializado por host e com retry de erros transitórios."""

        def _fazer() -> requests.Response:
            resposta = self._session.get(url, timeout=timeout, **kwargs)
            resposta.raise_for_status()
            return resposta

        with self._serializador.serializar(url):
            return executar_com_retry(_fazer, delays=self._retry_delays)

    def _get_json(self: "_FundosBase", endpoint: str, payload: dict[str, object]) -> object:
        """Executa o GET do endpoint informado com o token construído do payload."""
        token = self._build_token(payload)
        url = f"{_BASE_URL}/{endpoint}/{token}"
        logger.info("Consultando %s", url)
        return self._requisicao_get(url).json()

    def _get_listed_json(self: "_FundosBase", endpoint: str, payload: dict[str, object]) -> object:
        """Executa o GET do proxy de empresas listadas com token Base64."""
        token = self._build_token(payload)
        url = f"{_LISTED_BASE_URL}/{endpoint}/{token}"
        logger.info("Consultando %s", url)
        return self._requisicao_get(url).json()

    def _cache_com_fallback(
        self: "_FundosBase",
        chave: str,
        ttl_dias: int,
        fetch_fn: Callable[[], dict[str, object]],
    ) -> dict[str, object]:
        """Obtém do cache e, em falha de rede, serve o registro existente."""
        try:
            return self._cache.get_or_fetch(
                chave, ttl_days=ttl_dias, fetch_fn=fetch_fn
            )
        except requests.RequestException:
            anterior = self._cache.read_meta(chave)
            if anterior is None:
                raise
            logger.warning(
                "Falha ao atualizar %s; servindo cache", chave, exc_info=True
            )
            return anterior
