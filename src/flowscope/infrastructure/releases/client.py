"""Cliente HTTP para consultar a última release publicada no GitHub."""

import logging
from urllib.parse import urlsplit

import requests

from flowscope.domain.version import parse_version

logger = logging.getLogger("flowscope")

RELEASES_BASE_URL = "https://github.com/amaurycarvalho/flowscope/releases"
LATEST_RELEASE_URL = f"{RELEASES_BASE_URL}/latest"
_TAG_MARKER = "/releases/tag/"
_TIMEOUT_S = 5.0


def obter_ultima_release(timeout: float = _TIMEOUT_S) -> tuple[str, str] | None:
    """Retorna ``(versao, url)`` da última release publicada, ou ``None``.

    Segue o redirecionamento de ``/releases/latest`` e extrai a tag do caminho
    final. Timeout, falha de rede ou ausência de tag resultam em ``None``.
    """
    try:
        resposta = requests.get(
            LATEST_RELEASE_URL, allow_redirects=True, timeout=timeout
        )
    except requests.RequestException:
        logger.warning(
            "Falha ao consultar a última release do FlowScope", exc_info=True
        )
        return None
    return _extrair_release(resposta.url)


def _extrair_release(url_final: str) -> tuple[str, str] | None:
    """Extrai ``(versao, url)`` de um endereço ``.../releases/tag/vX.Y.Z``."""
    caminho = urlsplit(url_final or "").path
    if _TAG_MARKER not in caminho:
        return None
    tag = caminho.split(_TAG_MARKER, 1)[1].strip("/")
    if not tag or parse_version(tag) is None:
        return None
    versao = tag[1:] if tag[:1] in ("v", "V") else tag
    return versao, f"{RELEASES_BASE_URL}/tag/{tag}"
