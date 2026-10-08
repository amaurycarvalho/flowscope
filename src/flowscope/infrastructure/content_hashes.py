"""Hash SHA-256 e registro de hashes de conteúdo em arquivos JSON.

O registro associa cada hash SHA-256 ao caminho relativo canônico do arquivo,
por escopo: um arquivo por ticker para documentos e um arquivo global para as
notícias. A gravação é atômica, serializada por lock, e a leitura tolera
ausência e corrupção.
"""

import hashlib
import json
import logging
import re
import threading
from pathlib import Path

from flowscope.application.deduplicacao import DeduplicacaoConteudo
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório dos registros de hash de documentos.
DIRETORIO_HASHES = "document-hashes"

#: Subpasta das notícias, que abriga o registro global.
PASTA_NOTICIAS = "noticias"

#: Nome do arquivo do registro global de notícias.
_ARQUIVO_HASHES_NOTICIAS = "hashes.json"

#: Versão do schema persistido.
SCHEMA_VERSION_HASHES = 1

#: Caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")

#: Subpastas de fonte cujo pai é a raiz de cache.
_PASTAS_FONTES = frozenset(
    {"bdr", "informe-mensal", "documentos-relevantes", "noticias"}
)


def hash_sha256(data: bytes) -> str:
    """Calcula o hash SHA-256 de um conteúdo binário."""
    return hashlib.sha256(data).hexdigest()


def raiz_cache(base: Path) -> Path:
    """Retorna a raiz de cache a partir de uma raiz de fonte específica.

    Quando ``base`` é a subpasta nomeada da fonte (por exemplo,
    ``documentos-relevantes``), a raiz é o seu pai; diretórios já usados como
    raiz (por exemplo, um diretório de testes) são retornados inalterados.
    """
    caminho = Path(base)
    return caminho.parent if caminho.name in _PASTAS_FONTES else caminho


def caminho_hashes_documentos(cache_root: Path, ticker: str) -> Path:
    """Resolve o caminho do registro de hashes de um ticker."""
    seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
    return Path(cache_root) / DIRETORIO_HASHES / f"{seguro}.json"


def caminho_hashes_noticias(cache_root: Path) -> Path:
    """Resolve o caminho do registro global de hashes das notícias."""
    return Path(cache_root) / PASTA_NOTICIAS / _ARQUIVO_HASHES_NOTICIAS


def deduplicacao_documentos(
    cache_root: Path, ticker: str
) -> DeduplicacaoConteudo:
    """Monta o serviço de deduplicação de documentos de um ticker."""
    root = Path(cache_root)
    return DeduplicacaoConteudo(
        JsonHashStore(caminho_hashes_documentos(root, ticker)),
        hash_sha256,
        root,
    )


def deduplicacao_noticias(cache_root: Path) -> DeduplicacaoConteudo:
    """Monta o serviço de deduplicação global de notícias."""
    root = Path(cache_root)
    return DeduplicacaoConteudo(
        JsonHashStore(caminho_hashes_noticias(root)),
        hash_sha256,
        root,
    )


def hash_de_caminho(cache_root: Path, ticker: str, relativo: str) -> str | None:
    """Retorna o hash registrado para o caminho relativo do ticker, ou ``None``.

    Inverte o registro ``hash -> caminho relativo`` para identificar um
    documento pelo conteúdo sem reler o arquivo. Usado como chave de identidade
    do Relatório Gerencial no ledger de guidance.
    """
    registro = JsonHashStore(
        caminho_hashes_documentos(cache_root, ticker)
    ).registrados()
    for digest, alvo in registro.items():
        if alvo == relativo:
            return digest
    return None


class JsonHashStore:
    """Persiste o mapa ``hash -> caminho relativo`` de um escopo em JSON."""

    def __init__(self: "JsonHashStore", path: Path) -> None:
        """Inicializa o registro no caminho de arquivo informado."""
        self._path = Path(path)
        self._lock = threading.Lock()

    @property
    def path(self: "JsonHashStore") -> Path:
        """Retorna o caminho do arquivo de registro."""
        return self._path

    def canonico(self: "JsonHashStore", digest: str) -> str | None:
        """Retorna o caminho relativo canônico do hash, ou ``None``."""
        return self._registrados().get(digest)

    def registrados(self: "JsonHashStore") -> dict[str, str]:
        """Retorna uma cópia do mapa ``hash -> caminho relativo``."""
        return dict(self._registrados())

    def registrar(
        self: "JsonHashStore", digest: str, relativo: str
    ) -> None:
        """Registra o hash apontando para o caminho relativo informado."""
        with self._lock:
            hashes = self._registrados()
            hashes[digest] = relativo
            self._gravar(hashes)

    def remover(self: "JsonHashStore", digest: str) -> None:
        """Remove a entrada do hash informado."""
        with self._lock:
            hashes = self._registrados()
            if hashes.pop(digest, None) is not None:
                self._gravar(hashes)

    def remover_relativo(self: "JsonHashStore", relativo: str) -> None:
        """Remove qualquer entrada cujo canônico seja o caminho relativo."""
        with self._lock:
            hashes = self._registrados()
            filtrado = {
                digest: valor
                for digest, valor in hashes.items()
                if valor != relativo
            }
            if len(filtrado) != len(hashes):
                self._gravar(filtrado)

    def _registrados(self: "JsonHashStore") -> dict[str, str]:
        """Retorna o mapa de hashes tolerando formato inválido."""
        dados = self._carregar().get("hashes")
        if not isinstance(dados, dict):
            return {}
        return {
            chave: valor
            for chave, valor in dados.items()
            if isinstance(chave, str) and isinstance(valor, str)
        }

    def _carregar(self: "JsonHashStore") -> dict:
        """Carrega o documento do registro, tolerando ausência e corrupção."""
        if not self._path.exists():
            return {}
        try:
            dados = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Registro de hashes corrompido: %s", self._path)
            return {}
        return dados if isinstance(dados, dict) else {}

    def _gravar(self: "JsonHashStore", hashes: dict[str, str]) -> None:
        """Grava o mapa de hashes de forma atômica."""
        payload = json.dumps(
            {"schema_version": SCHEMA_VERSION_HASHES, "hashes": hashes},
            ensure_ascii=False,
        ).encode("utf-8")
        _atomic_write_bytes(self._path, payload)
