"""Consulta de releases publicadas do FlowScope no repositório GitHub."""

from flowscope.infrastructure.releases.client import (
    LATEST_RELEASE_URL,
    RELEASES_BASE_URL,
    obter_ultima_release,
)

__all__ = ["LATEST_RELEASE_URL", "RELEASES_BASE_URL", "obter_ultima_release"]
