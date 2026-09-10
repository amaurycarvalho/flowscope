"""Download genérico de datasets anuais da CVM (RFC-009/010).

Baixa, extrai, calcula hash e persiste o arquivo bruto e metadados sob o cache
do FlowScope, reutilizando o arquivo local quando já existir.
"""

import hashlib
import io
import json
import logging
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import requests

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache import (
    ConditionalCache,
    RevalidationResult,
    RevalidationStatus,
    headers_to_validators,
)

logger = logging.getLogger("flowscope")

#: Intervalo mínimo padrão entre revalidações remotas do arquivo anual.
_REVALIDATE_AFTER_PADRAO = timedelta(hours=6)


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
        probe: Callable[[int, Mapping[str, str]], RevalidationResult] | None = None,
        revalidate_after: timedelta = _REVALIDATE_AFTER_PADRAO,
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
        self._probe = probe or (self._probe_http if fetch is None else None)
        self._revalidate_after = revalidate_after
        self._conditional = ConditionalCache()

    def url_anual(self: "CvmDatasetDownloader", ano: int) -> str:
        """Retorna a URL do arquivo anual."""
        return f"{self._base_url}/{self._arquivo(ano)}"

    def baixar_ano(self: "CvmDatasetDownloader", ano: int) -> bytes:
        """Retorna o arquivo anual, revalidando a fonte antes de reutilizá-lo."""
        resultado = self._conditional.get_file_or_revalidate(
            self._caminho(ano),
            fetch=lambda: self._obter(ano),
            probe=(lambda validators: self._probe(ano, validators))
            if self._probe is not None
            else None,
            read_validators=lambda: self._ler_validadores(ano),
            write_metadata=lambda data, validators, agora: self._persistir(
                ano, data, validators, agora
            ),
            revalidate_after=self._revalidate_after,
        )
        return resultado.data

    def _obter(self: "CvmDatasetDownloader", ano: int) -> tuple[bytes, Mapping[str, str]]:
        """Obtém o arquivo e os validadores, tolerando loaders que devolvem bytes."""
        resultado = self._fetch(ano)
        if isinstance(resultado, tuple):
            return resultado
        return resultado, {}

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

    def _persistir(
        self: "CvmDatasetDownloader",
        ano: int,
        data: bytes,
        validators: Mapping[str, str] | None = None,
        revalidated_at: datetime | None = None,
    ) -> None:
        """Grava o arquivo bruto, o hash e os metadados do ano."""
        caminho = self._caminho(ano)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(data)
        digest = hash_sha256(data)
        (caminho.parent / "SHA256").write_text(digest, encoding="utf-8")
        anterior = self._ler_metadados(ano)
        agora = datetime.now(timezone.utc)
        baixado_em = (
            anterior.get("downloaded_at")
            if anterior and anterior.get("sha256") == digest
            else agora.isoformat()
        )
        metadata = {
            "dataset": self._dataset,
            "year": ano,
            "url": self.url_anual(ano),
            "downloaded_at": baixado_em,
            "sha256": digest,
            "parser_version": self._parser_version,
            **(validators or {}),
            "revalidated_at": (revalidated_at or agora).isoformat(),
        }
        (caminho.parent / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def _baixar_http(
        self: "CvmDatasetDownloader", ano: int
    ) -> tuple[bytes, Mapping[str, str]]:
        """Baixa o arquivo anual via HTTP, devolvendo validadores remotos."""
        url = self.url_anual(ano)
        logger.info("Baixando dataset CVM %s via %s", self._dataset, url)
        resposta = self._session.get(url, timeout=60)
        resposta.raise_for_status()
        return resposta.content, headers_to_validators(resposta.headers)

    def _probe_http(
        self: "CvmDatasetDownloader", ano: int, validators: Mapping[str, str]
    ) -> RevalidationResult:
        """Verifica a fonte remota por HEAD, com fallback para GET condicional."""
        url = self.url_anual(ano)
        headers: dict[str, str] = {}
        if validators.get("last_modified"):
            headers["If-Modified-Since"] = validators["last_modified"]
        if validators.get("etag"):
            headers["If-None-Match"] = validators["etag"]
        try:
            resposta = self._session.head(url, headers=headers, timeout=30)
        except requests.RequestException:
            resposta = None
        if resposta is not None and resposta.status_code == 304:
            return RevalidationResult(
                RevalidationStatus.UNCHANGED,
                validators=headers_to_validators(resposta.headers),
            )
        if resposta is not None and resposta.status_code < 400:
            return resultado_por_tamanho(validators, resposta.headers)
        resposta = self._session.get(url, headers=headers, timeout=60)
        if resposta.status_code == 304:
            return RevalidationResult(
                RevalidationStatus.UNCHANGED,
                validators=headers_to_validators(resposta.headers),
            )
        if resposta.status_code >= 400:
            return RevalidationResult(RevalidationStatus.UNKNOWN)
        return RevalidationResult(
            RevalidationStatus.CHANGED,
            validators=headers_to_validators(resposta.headers),
        )

    def _ler_metadados(
        self: "CvmDatasetDownloader", ano: int
    ) -> dict[str, object] | None:
        """Lê os metadados do ano, ou ``None`` quando ausentes/corrompidos."""
        caminho = self._caminho(ano).parent / "metadata.json"
        if not caminho.exists():
            return None
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return dados if isinstance(dados, dict) else None

    def _ler_validadores(self: "CvmDatasetDownloader", ano: int) -> dict[str, str]:
        """Retorna os validadores remotos registrados para o ano."""
        dados = self._ler_metadados(ano) or {}
        return {
            chave: str(dados[chave])
            for chave in ("etag", "last_modified", "content_length", "revalidated_at")
            if dados.get(chave)
        }

    def _caminho(self: "CvmDatasetDownloader", ano: int) -> Path:
        """Retorna o caminho local do arquivo anual."""
        return self._base / str(ano) / self._arquivo(ano)


def resultado_por_tamanho(
    validators: Mapping[str, str], headers: Mapping[str, str]
) -> RevalidationResult:
    """Decide a revalidação comparando validadores HTTP armazenados e remotos."""
    novos = headers_to_validators(headers)
    if validators.get("last_modified") and (
        novos.get("last_modified") == validators.get("last_modified")
    ):
        return RevalidationResult(RevalidationStatus.UNCHANGED, validators=novos)
    anterior = validators.get("content_length")
    remoto = novos.get("content_length")
    if anterior and remoto and anterior == remoto:
        return RevalidationResult(RevalidationStatus.UNCHANGED, validators=novos)
    return RevalidationResult(RevalidationStatus.CHANGED, validators=novos)
