import json
import platform
import sys
from datetime import date, datetime
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or self._default_cache_dir()

    def _default_cache_dir(self) -> Path:
        system = platform.system()
        if system == "Linux":
            base = Path.home() / ".cache" / "flowscope"
        elif system == "Windows":
            local_appdata = Path(
                sys.executable or ""
            ).parent.parent / "Local" / "flowscope" / "cache"
            base = Path.home() / "AppData" / "Local" / "flowscope" / "cache"
        elif system == "Darwin":
            base = Path.home() / "Library" / "Caches" / "flowscope"
        else:
            base = Path.home() / ".cache" / "flowscope"
        return base

    def get_cache_dir(self) -> Path:
        return self._cache_dir

    def _path_for(self, d: date) -> Path:
        return self._cache_dir / f"{d.strftime('%Y-%m-%d')}.csv"

    def get(self, d: date) -> str | None:
        path = self._path_for(d)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def put(self, d: date, content: str) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._path_for(d)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(path)

    def _meta_path_for(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def invalidate(self, key: str) -> None:
        meta_path = self._meta_path_for(key)
        if meta_path.exists():
            meta_path.unlink()

    def get_or_fetch(self, key: str, ttl_days: int, fetch_fn) -> dict:
        meta_path = self._meta_path_for(key)
        if meta_path.exists():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(data["cached_at"])
                delta = datetime.now() - cached_at
                if delta.days < ttl_days:
                    return data
            except (KeyError, ValueError, json.JSONDecodeError):
                pass
        result = fetch_fn()
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {"cached_at": datetime.now().isoformat(), **result}
        tmp = meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        tmp.rename(meta_path)
        return payload
