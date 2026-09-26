"""Persistência dos resumos de documentos em JSON por ticker.

Cada ticker tem um arquivo em ``~/.cache/flowscope/document-summaries/`` que
mapeia a chave estável do documento — o caminho relativo à raiz de cache — para
o par de resumos. A leitura tolera arquivo ausente ou corrompido e a gravação é
atômica, preservando os resumos dos demais documentos.
"""

import json
import logging
import re
import threading
from pathlib import Path

from flowscope.application.documentos.catalogo import chave_documento
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

__all__ = [
    "DIRETORIO_RESUMOS",
    "SCHEMA_VERSION_RESUMOS",
    "JsonDocumentSummaryStore",
    "chave_documento",
]

#: Subdiretório dos resumos dentro do diretório de cache.
DIRETORIO_RESUMOS = "document-summaries"

#: Versão do schema persistido.
SCHEMA_VERSION_RESUMOS = 1

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


class JsonDocumentSummaryStore(DocumentSummaryStore):
    """Armazena resumos por ticker em arquivos JSON com escrita atômica.

    Adaptador concreto da porta ``DocumentSummaryStore``. O *read-modify-write*
    de :meth:`salvar` é serializado por um lock para que gravações concorrentes
    não percam resumos.
    """

    def __init__(
        self: "JsonDocumentSummaryStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no subdiretório de resumos do cache informado."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_RESUMOS
        self._lock = threading.Lock()

    def resumos(
        self: "JsonDocumentSummaryStore", ticker: str
    ) -> dict[str, ResumoDocumento]:
        """Retorna os resumos do ticker, indexados pela chave do documento."""
        resultado: dict[str, ResumoDocumento] = {}
        for chave, registro in self._carregar(ticker).items():
            if not isinstance(registro, dict):
                continue
            resultado[chave] = ResumoDocumento(
                short_summary=_texto(registro.get("short_summary")),
                long_summary=_texto(registro.get("long_summary")),
            )
        return resultado

    def obter(
        self: "JsonDocumentSummaryStore", ticker: str, chave: str
    ) -> ResumoDocumento | None:
        """Retorna o resumo de um documento, ou ``None`` quando ausente."""
        return self.resumos(ticker).get(chave)

    def salvar(
        self: "JsonDocumentSummaryStore",
        ticker: str,
        chave: str,
        short_summary: str,
        long_summary: str,
    ) -> None:
        """Grava o resumo de um documento preservando os demais do ticker.

        O *read-modify-write* é serializado por um lock para que gravações
        concorrentes — por exemplo, o lote de resumos e a pré-visualização
        individual — não percam resumos já gravados.
        """
        with self._lock:
            resumos = self._carregar(ticker)
            resumos[chave] = {
                "short_summary": short_summary,
                "long_summary": long_summary,
            }
            self._gravar(ticker, resumos)

    def _carregar(self: "JsonDocumentSummaryStore", ticker: str) -> dict:
        """Carrega o mapa de resumos, tolerando ausência e corrupção."""
        caminho = self._path_for(ticker)
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Resumos de documentos corrompidos: %s", caminho)
            return {}
        if not isinstance(dados, dict):
            return {}
        resumos = dados.get("resumos")
        return resumos if isinstance(resumos, dict) else {}

    def _gravar(self: "JsonDocumentSummaryStore", ticker: str, resumos: dict) -> None:
        """Grava o mapa de resumos do ticker de forma atômica."""
        payload = json.dumps(
            {"schema_version": SCHEMA_VERSION_RESUMOS, "resumos": resumos},
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        _atomic_write_bytes(self._path_for(ticker), payload)

    def _path_for(self: "JsonDocumentSummaryStore", ticker: str) -> Path:
        """Resolve o caminho do arquivo de resumos de um ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"


def _texto(valor: object) -> str:
    """Normaliza um valor persistido para string, tolerando tipos inválidos."""
    return valor if isinstance(valor, str) else ""
