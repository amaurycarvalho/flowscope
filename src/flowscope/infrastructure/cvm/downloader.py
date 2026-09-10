"""Download, hash e cache do ZIP anual do Informe Mensal da CVM (RFC-009)."""

import hashlib
import io
import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import requests

from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")

#: Diretório oficial dos dados abertos do Informe Mensal de FIIs.
CVM_BASE_URL = "https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS"

#: Versão do parser/aquisição registrada nos metadados.
PARSER_VERSION = "cvm-inf-mensal-v1"


def url_anual(ano: int) -> str:
    """Retorna a URL do arquivo anual do Informe Mensal."""
    return f"{CVM_BASE_URL}/inf_mensal_fii_{ano}.zip"


def hash_sha256(data: bytes) -> str:
    """Calcula o hash SHA-256 de um conteúdo binário."""
    return hashlib.sha256(data).hexdigest()


class CvmMonthlyDownloader:
    """Baixa, extrai e cacheia os arquivos anuais do Informe Mensal."""

    def __init__(
        self: "CvmMonthlyDownloader",
        cache_dir: Path | None = None,
        session: requests.Session | None = None,
        fetch: Callable[[int], bytes] | None = None,
        parser_version: str = PARSER_VERSION,
    ) -> None:
        """Inicializa o downloader com diretório, sessão e loader opcionais."""
        base = cache_dir or (CacheManager().get_cache_dir() / "cvm" / "inf_mensal")
        self._base = Path(base)
        self._session = session or requests.Session()
        self._fetch = fetch or self._baixar_http
        self._parser_version = parser_version

    def baixar_ano(self: "CvmMonthlyDownloader", ano: int) -> bytes:
        """Retorna o ZIP anual, baixando e persistindo quando ainda não cacheado."""
        zip_path = self._zip_path(ano)
        if zip_path.exists():
            return zip_path.read_bytes()
        data = self._fetch(ano)
        self._persistir(ano, data)
        return data

    def extrair_csvs(
        self: "CvmMonthlyDownloader", data: bytes
    ) -> dict[str, bytes]:
        """Extrai todos os arquivos CSV contidos no ZIP."""
        resultado: dict[str, bytes] = {}
        with ZipFile(io.BytesIO(data)) as arquivo:
            for nome in arquivo.namelist():
                if nome.lower().endswith(".csv"):
                    resultado[nome] = arquivo.read(nome)
        return resultado

    def _persistir(self: "CvmMonthlyDownloader", ano: int, data: bytes) -> None:
        """Grava o ZIP bruto, o hash e os metadados do ano."""
        diretorio = self._base / str(ano)
        diretorio.mkdir(parents=True, exist_ok=True)
        (diretorio / f"inf_mensal_fii_{ano}.zip").write_bytes(data)
        digest = hash_sha256(data)
        (diretorio / "SHA256").write_text(digest, encoding="utf-8")
        metadata = {
            "dataset": "FII-INF-MENSAL",
            "year": ano,
            "url": url_anual(ano),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "sha256": digest,
            "parser_version": self._parser_version,
        }
        (diretorio / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def _baixar_http(self: "CvmMonthlyDownloader", ano: int) -> bytes:
        """Baixa o ZIP anual via HTTP."""
        url = url_anual(ano)
        logger.info("Baixando informe mensal CVM via %s", url)
        resposta = self._session.get(url, timeout=60)
        resposta.raise_for_status()
        return resposta.content

    def _zip_path(self: "CvmMonthlyDownloader", ano: int) -> Path:
        """Retorna o caminho local do ZIP anual."""
        return self._base / str(ano) / f"inf_mensal_fii_{ano}.zip"
