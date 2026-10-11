"""Registro de URLs baixadas com sucesso, por escopo, em arquivos JSON.

O registro associa cada URL normalizada ao caminho relativo canônico do arquivo
persistido, impedindo nova requisição da mesma URL mesmo quando a data, o slug
de categoria ou o caminho derivado mudarem entre execuções. O escopo é por
ticker para os documentos e único e global para as notícias. A gravação é
atômica, serializada por lock, e a leitura tolera ausência e corrupção.

É independente do registro de hashes de conteúdo (``content_hashes``): este
evita a requisição antes de o conteúdo existir; aquele deduplica conteúdo
idêntico servido por URLs distintas.
"""

import json
import logging
import re
import threading
from pathlib import Path

from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório dos registros de URL de documentos.
DIRETORIO_URLS = "url-downloads"

#: Subpasta das notícias, que abriga o registro global.
PASTA_NOTICIAS = "noticias"

#: Nome do arquivo do registro global de notícias.
_ARQUIVO_URLS_NOTICIAS = "url-downloads.json"

#: Versão do schema persistido.
SCHEMA_VERSION_URLS = 1

#: Caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


def normalizar_url(url: str) -> str:
    """Normaliza a URL para servir de chave determinista do registro."""
    return (url or "").strip()


def caminho_urls_documentos(cache_root: Path, ticker: str) -> Path:
    """Resolve o caminho do registro de URLs de um ticker."""
    seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
    return Path(cache_root) / DIRETORIO_URLS / f"{seguro}.json"


def caminho_urls_noticias(cache_root: Path) -> Path:
    """Resolve o caminho do registro global de URLs das notícias."""
    return Path(cache_root) / PASTA_NOTICIAS / _ARQUIVO_URLS_NOTICIAS


def url_store_documentos(cache_root: Path, ticker: str) -> "JsonUrlStore":
    """Monta o registro de URLs dos documentos de um ticker."""
    return JsonUrlStore(caminho_urls_documentos(cache_root, ticker))


def url_store_noticias(cache_root: Path) -> "JsonUrlStore":
    """Monta o registro global de URLs das notícias."""
    return JsonUrlStore(caminho_urls_noticias(cache_root))


class JsonUrlStore:
    """Persiste o mapa ``url -> caminho relativo`` de um escopo em JSON."""

    def __init__(self: "JsonUrlStore", path: Path) -> None:
        """Inicializa o registro no caminho de arquivo informado."""
        self._path = Path(path)
        self._lock = threading.Lock()

    @property
    def path(self: "JsonUrlStore") -> Path:
        """Retorna o caminho do arquivo de registro."""
        return self._path

    def canonico(self: "JsonUrlStore", url: str) -> str | None:
        """Retorna o caminho relativo canônico da URL, ou ``None``."""
        return self._registrados().get(normalizar_url(url))

    def registrados(self: "JsonUrlStore") -> dict[str, str]:
        """Retorna uma cópia do mapa ``url -> caminho relativo``."""
        return dict(self._registrados())

    def registrar(self: "JsonUrlStore", url: str, relativo: str) -> None:
        """Registra a URL apontando para o caminho relativo informado."""
        chave = normalizar_url(url)
        if not chave:
            return
        with self._lock:
            dados = self._registrados()
            dados[chave] = relativo
            self._gravar(dados)

    def remover(self: "JsonUrlStore", url: str) -> None:
        """Remove a entrada da URL informada."""
        with self._lock:
            dados = self._registrados()
            if dados.pop(normalizar_url(url), None) is not None:
                self._gravar(dados)

    def remover_relativo(self: "JsonUrlStore", relativo: str) -> None:
        """Remove qualquer entrada cujo canônico seja o caminho relativo."""
        with self._lock:
            dados = self._registrados()
            filtrado = {
                url: valor
                for url, valor in dados.items()
                if valor != relativo
            }
            if len(filtrado) != len(dados):
                self._gravar(filtrado)

    def _registrados(self: "JsonUrlStore") -> dict[str, str]:
        """Retorna o mapa de URLs tolerando formato inválido."""
        dados = self._carregar().get("urls")
        if not isinstance(dados, dict):
            return {}
        return {
            chave: valor
            for chave, valor in dados.items()
            if isinstance(chave, str) and isinstance(valor, str)
        }

    def _carregar(self: "JsonUrlStore") -> dict:
        """Carrega o documento do registro, tolerando ausência e corrupção."""
        if not self._path.exists():
            return {}
        try:
            dados = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Registro de URLs corrompido: %s", self._path)
            return {}
        return dados if isinstance(dados, dict) else {}

    def _gravar(self: "JsonUrlStore", urls: dict[str, str]) -> None:
        """Grava o mapa de URLs de forma atômica."""
        payload = json.dumps(
            {"schema_version": SCHEMA_VERSION_URLS, "urls": urls},
            ensure_ascii=False,
        ).encode("utf-8")
        _atomic_write_bytes(self._path, payload)
