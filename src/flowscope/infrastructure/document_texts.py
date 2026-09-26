"""Persistência do texto extraído dos documentos em JSON por ticker.

Cada ticker tem um arquivo em ``~/.cache/flowscope/document-texts/`` que mapeia
a chave estável do documento — o caminho relativo à raiz de cache — para o
texto original extraído (ou o marcador de ausência de texto). A leitura tolera
arquivo ausente ou corrompido e a gravação é atômica, preservando os textos dos
demais documentos.
"""

import json
import logging
import re
from pathlib import Path

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório dos textos dentro do diretório de cache.
DIRETORIO_TEXTOS = "document-texts"

#: Versão do schema persistido.
SCHEMA_VERSION_TEXTOS = 1

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


class JsonDocumentTextStore(DocumentTextStore):
    """Armazena textos de documentos por ticker em JSON com escrita atômica."""

    def __init__(
        self: "JsonDocumentTextStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no subdiretório de textos do cache informado."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_TEXTOS

    def textos(self: "JsonDocumentTextStore", ticker: str) -> dict[str, str]:
        """Retorna os textos do ticker, indexados pela chave do documento."""
        resultado: dict[str, str] = {}
        for chave, valor in self._carregar(ticker).items():
            if isinstance(valor, str):
                resultado[chave] = valor
        return resultado

    def obter(
        self: "JsonDocumentTextStore", ticker: str, chave: str
    ) -> str | None:
        """Retorna o texto de um documento, ou ``None`` quando ausente."""
        return self.textos(ticker).get(chave)

    def salvar(
        self: "JsonDocumentTextStore", ticker: str, chave: str, texto: str
    ) -> None:
        """Grava o texto de um documento preservando os demais do ticker."""
        textos = self._carregar(ticker)
        textos[chave] = texto
        self._gravar(ticker, textos)

    def _carregar(self: "JsonDocumentTextStore", ticker: str) -> dict:
        """Carrega o mapa de textos, tolerando ausência e corrupção."""
        caminho = self._path_for(ticker)
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Textos de documentos corrompidos: %s", caminho)
            return {}
        if not isinstance(dados, dict):
            return {}
        textos = dados.get("textos")
        return textos if isinstance(textos, dict) else {}

    def _gravar(self: "JsonDocumentTextStore", ticker: str, textos: dict) -> None:
        """Grava o mapa de textos do ticker de forma atômica."""
        payload = json.dumps(
            {"schema_version": SCHEMA_VERSION_TEXTOS, "textos": textos},
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        _atomic_write_bytes(self._path_for(ticker), payload)

    def _path_for(self: "JsonDocumentTextStore", ticker: str) -> Path:
        """Resolve o caminho do arquivo de textos de um ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"
