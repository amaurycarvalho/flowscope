"""Leitura e escrita atômica do snapshot estável de performance.

O snapshot vive em ``~/.cache/flowscope/performance/latest.json`` e é a fonte de
leitura do chat, da CLI de leitura e do servidor MCP. A leitura tolera ausência,
JSON inválido, resultado não-dicionário e schema divergente, tratando todos como
ausência de resultado; a escrita é atômica e não propaga falhas de I/O.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from flowscope.application.performance.snapshot import (
    SCHEMA_VERSION_SNAPSHOT,
    snapshot_de_dict,
)
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes
from flowscope.infrastructure.performance.cache import DIRETORIO_PERFORMANCE

logger = logging.getLogger("flowscope")

#: Nome do arquivo do snapshot mais recente.
ARQUIVO_SNAPSHOT = "latest.json"


class JsonPerformanceSnapshotStore:
    """Persiste e lê o snapshot mais recente dos resultados de performance."""

    def __init__(
        self: JsonPerformanceSnapshotStore, cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no diretório informado ou no padrão do sistema."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._caminho = Path(base) / DIRETORIO_PERFORMANCE / ARQUIVO_SNAPSHOT

    @property
    def caminho(self: JsonPerformanceSnapshotStore) -> Path:
        """Caminho do arquivo do snapshot."""
        return self._caminho

    def ler(self: JsonPerformanceSnapshotStore) -> dict | None:
        """Devolve o snapshot válido, ou ``None`` quando ausente/inválido."""
        if not self._caminho.exists():
            return None
        try:
            dados = json.loads(self._caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning(
                "Performance: snapshot ilegível em %s; tratando como ausente",
                self._caminho,
            )
            return None
        snapshot = snapshot_de_dict(dados)
        if snapshot is None:
            _registrar_problema(self._caminho, dados)
        return snapshot

    def gravar(self: JsonPerformanceSnapshotStore, snapshot: dict) -> bool:
        """Grava o snapshot de forma atômica; devolve ``False`` em falha de I/O."""
        try:
            _atomic_write_bytes(
                self._caminho,
                json.dumps(snapshot, ensure_ascii=False, default=str).encode("utf-8"),
            )
        except OSError:
            logger.warning(
                "Performance: falha ao gravar o snapshot em %s; "
                "o resultado anterior, se houver, permanece",
                self._caminho,
                exc_info=True,
            )
            return False
        return True


def _registrar_problema(caminho: Path, dados: object) -> None:
    """Registra a causa específica de um snapshot rejeitado."""
    if not isinstance(dados, dict):
        logger.warning(
            "Performance: snapshot em %s não é um objeto; tratando como ausente",
            caminho,
        )
        return
    if not isinstance(dados.get("results"), dict):
        logger.warning(
            "Performance: snapshot em %s sem objeto de resultados; "
            "tratando como ausente",
            caminho,
        )
        return
    if dados.get("schema_version") != SCHEMA_VERSION_SNAPSHOT:
        logger.warning(
            "Performance: snapshot em %s com schema divergente (%s != %s); "
            "tratando como ausente",
            caminho,
            dados.get("schema_version"),
            SCHEMA_VERSION_SNAPSHOT,
        )
        return
    logger.warning(
        "Performance: snapshot em %s inválido; tratando como ausente", caminho
    )
