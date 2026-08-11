"""Gerencia o cache em disco de dados baixados e metadados do FlowScope."""

import json
import platform
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


class CacheManager:
    """Gerencia arquivos de cache em disco com controle de expiração."""

    def __init__(self: "CacheManager", cache_dir: Path | None = None) -> None:
        """Inicializa o gerenciador de cache com o diretório informado ou o padrão do sistema."""
        self._cache_dir = cache_dir or self._default_cache_dir()

    def _default_cache_dir(self: "CacheManager") -> Path:
        system = platform.system()
        if system == "Linux":
            base = Path.home() / ".cache" / "flowscope"
        elif system == "Windows":
            base = Path.home() / "AppData" / "Local" / "flowscope" / "cache"
        elif system == "Darwin":
            base = Path.home() / "Library" / "Caches" / "flowscope"
        else:
            base = Path.home() / ".cache" / "flowscope"
        return base

    def get_cache_dir(self: "CacheManager") -> Path:
        """Retorna o diretório raiz do cache."""
        return self._cache_dir

    def _path_for(self: "CacheManager", d: date) -> Path:
        return self._cache_dir / f"{d.strftime('%Y-%m-%d')}.csv"

    def get(self: "CacheManager", d: date) -> str | None:
        """Retorna o conteúdo em cache para a data, ou None se não existir."""
        path = self._path_for(d)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def find_nearest(self: "CacheManager", d: date, max_deviation: int = 7) -> date | None:
        """Busca a data com cache mais próxima da data informada, dentro da tolerância."""
        for delta_days in range(max_deviation + 1):
            for candidate in (d - timedelta(days=delta_days), d + timedelta(days=delta_days)):
                if self._path_for(candidate).exists():
                    return candidate
                if delta_days == 0:
                    break
        return None

    def put(self: "CacheManager", d: date, content: str) -> None:
        """Grava o conteúdo no cache da data informada, de forma atômica."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(d)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)

    def _meta_path_for(self: "CacheManager", key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def invalidate(self: "CacheManager", key: str) -> None:
        """Remove o arquivo de metadados em cache para a chave informada."""
        meta_path = self._meta_path_for(key)
        if meta_path.exists():
            meta_path.unlink()

    def get_or_fetch(self: "CacheManager", key: str, ttl_days: int,
                     fetch_fn: Callable[[], dict[str, object]]) -> dict[str, object]:
        """Retorna o cache da chave se ainda válido; caso contrário, busca e armazena novo valor."""
        meta_path = self._meta_path_for(key)
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(data["cached_at"])
                if cached_at.tzinfo is None:
                    cached_at = cached_at.replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - cached_at
                if delta.days < ttl_days:
                    return data
            except (KeyError, ValueError, json.JSONDecodeError):
                pass
        result = fetch_fn()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {"cached_at": datetime.now(timezone.utc).isoformat(), **result}
        tmp = meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        tmp.rename(meta_path)
        return payload
