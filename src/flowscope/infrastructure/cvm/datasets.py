"""Download genérico de datasets anuais da CVM (RFC-009/010).

Baixa, extrai, calcula hash e persiste o arquivo bruto e metadados sob o cache
do FlowScope, reutilizando o arquivo local quando já existir.
"""

import hashlib
import io
import json
import logging
from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import requests

from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")


def hash_sha256(data: bytes) -> str:
    """Calcula o hash SHA-256 de um conteúdo binário."""
    return hashlib.sha256(data).hexdigest()


def parse_data(valor: object) -> date | None:
    """Interpreta uma data ISO (``AAAA-MM-DD``) ou brasileira (``DD/MM/AAAA``)."""
    if not valor:
        return None
    texto = str(valor).strip()[:10]
    if "-" in texto:
        partes = texto.split("-")
        ano, mes, dia = partes[0], partes[1], partes[2]
    elif "/" in texto:
        partes = texto.split("/")
        dia, mes, ano = partes[0], partes[1], partes[2]
    else:
        return None
    try:
        return date(int(ano), int(mes), int(dia))
    except ValueError:
        return None


def parse_decimal(valor: object) -> Decimal | None:
    """Interpreta um valor monetário brasileiro como ``Decimal``, ou ``None``."""
    from decimal import InvalidOperation

    from flowscope.infrastructure.fii.parsing import moeda_para_decimal

    if valor is None:
        return None
    try:
        return moeda_para_decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def parse_inteiro(valor: object) -> int:
    """Interpreta um valor como inteiro, retornando zero quando inválido."""
    try:
        return int(str(valor))
    except (TypeError, ValueError):
        return 0


class CvmDatasetDownloader:
    """Baixa e cacheia um dataset anual da CVM, em ZIP ou CSV."""

    def __init__(
        self: "CvmDatasetDownloader",
        base_url: str,
        arquivo: Callable[[int], str],
        dataset: str,
        cache_dir: Path | None = None,
        session: requests.Session | None = None,
        fetch: Callable[[int], bytes] | None = None,
        parser_version: str = "cvm-v1",
        zipado: bool = True,
    ) -> None:
        """Inicializa o downloader com a URL base, o nome e o cache do dataset."""
        self._base_url = base_url
        self._arquivo = arquivo
        self._dataset = dataset
        base = cache_dir or (CacheManager().get_cache_dir() / "cvm" / dataset)
        self._base = Path(base)
        self._session = session or requests.Session()
        self._fetch = fetch or self._baixar_http
        self._parser_version = parser_version
        self._zipado = zipado

    def url_anual(self: "CvmDatasetDownloader", ano: int) -> str:
        """Retorna a URL do arquivo anual."""
        return f"{self._base_url}/{self._arquivo(ano)}"

    def baixar_ano(self: "CvmDatasetDownloader", ano: int) -> bytes:
        """Retorna o arquivo anual, baixando e persistindo quando necessário."""
        caminho = self._caminho(ano)
        if caminho.exists():
            return caminho.read_bytes()
        data = self._fetch(ano)
        self._persistir(ano, data)
        return data

    def extrair_csvs(
        self: "CvmDatasetDownloader", data: bytes, ano: int
    ) -> dict[str, bytes]:
        """Extrai os CSVs do arquivo (ou devolve o próprio CSV)."""
        if not self._zipado:
            return {self._arquivo(ano): data}
        resultado: dict[str, bytes] = {}
        with ZipFile(io.BytesIO(data)) as arquivo:
            for nome in arquivo.namelist():
                if nome.lower().endswith(".csv"):
                    resultado[nome] = arquivo.read(nome)
        return resultado

    def _persistir(self: "CvmDatasetDownloader", ano: int, data: bytes) -> None:
        """Grava o arquivo bruto, o hash e os metadados do ano."""
        caminho = self._caminho(ano)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(data)
        digest = hash_sha256(data)
        (caminho.parent / "SHA256").write_text(digest, encoding="utf-8")
        metadata = {
            "dataset": self._dataset,
            "year": ano,
            "url": self.url_anual(ano),
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "sha256": digest,
            "parser_version": self._parser_version,
        }
        (caminho.parent / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def _baixar_http(self: "CvmDatasetDownloader", ano: int) -> bytes:
        """Baixa o arquivo anual via HTTP."""
        url = self.url_anual(ano)
        logger.info("Baixando dataset CVM %s via %s", self._dataset, url)
        resposta = self._session.get(url, timeout=60)
        resposta.raise_for_status()
        return resposta.content

    def _caminho(self: "CvmDatasetDownloader", ano: int) -> Path:
        """Retorna o caminho local do arquivo anual."""
        return self._base / str(ano) / self._arquivo(ano)
