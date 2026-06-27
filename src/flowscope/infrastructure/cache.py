import platform
import sys
from datetime import date
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
