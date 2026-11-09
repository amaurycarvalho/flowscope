"""Cache JSON dos resultados de performance por benchmark.

Um arquivo por chave lógica ``(schema, índice, data de referência, período,
amostragem, tickers ordenados, base de retorno)``. A escrita é atômica e a
leitura tolera arquivos corrompidos, tratando-os como ausência de cache.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from flowscope.application.performance.modelos import PerformanceCacheKey
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório padrão dos resultados de performance dentro do cache.
DIRETORIO_PERFORMANCE = "performance"


class JsonPerformanceCache:
    """Implementa o read-through dos resultados de performance em JSON."""

    def __init__(
        self: "JsonPerformanceCache", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o cache no diretório informado ou no padrão do sistema."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_PERFORMANCE

    def obter(self: "JsonPerformanceCache", chave: PerformanceCacheKey) -> dict | None:
        """Retorna o resultado em cache, ou ``None`` quando ausente/corrompido."""
        caminho = self._path_for(chave)
        if not caminho.exists():
            return None
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Cache de performance corrompido: %s", caminho)
            return None
        if not isinstance(dados, dict):
            return None
        if dados.get("schema_version") != chave.schema_version:
            return None
        resultado = dados.get("resultado")
        return resultado if isinstance(resultado, dict) else None

    def registrar(
        self: "JsonPerformanceCache",
        chave: PerformanceCacheKey,
        resultado: dict,
    ) -> None:
        """Grava o resultado do benchmark de forma atômica."""
        payload = {
            "schema_version": chave.schema_version,
            "chave": chave.identidade(),
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "resultado": resultado,
        }
        try:
            _atomic_write_bytes(
                self._path_for(chave),
                json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"),
            )
        except OSError:
            logger.warning(
                "Falha ao gravar o cache de performance de %s; "
                "resultado segue apenas em memória",
                chave.index,
                exc_info=True,
            )

    def _path_for(self: "JsonPerformanceCache", chave: PerformanceCacheKey) -> Path:
        """Resolve o caminho do arquivo a partir da identidade da chave."""
        digest = hashlib.sha256(chave.identidade().encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"
