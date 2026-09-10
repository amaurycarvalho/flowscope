"""Download, hash e cache do ZIP anual do Informe Mensal da CVM (RFC-009)."""

import hashlib
import io
import json
import logging
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta, timezone
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
from flowscope.infrastructure.cvm.datasets import resultado_por_tamanho

logger = logging.getLogger("flowscope")

#: Intervalo mínimo padrão entre revalidações remotas do arquivo anual.
_REVALIDATE_AFTER_PADRAO = timedelta(hours=6)

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
        probe: Callable[[int, Mapping[str, str]], RevalidationResult] | None = None,
        revalidate_after: timedelta = _REVALIDATE_AFTER_PADRAO,
    ) -> None:
        """Inicializa o downloader com diretório, sessão e loader opcionais."""
        base = cache_dir or (CacheManager().get_cache_dir() / "cvm" / "inf_mensal")
        self._base = Path(base)
        self._session = session or requests.Session()
        self._fetch = fetch or self._baixar_http
        self._parser_version = parser_version
        self._probe = probe or (self._probe_http if fetch is None else None)
        self._revalidate_after = revalidate_after
        self._conditional = ConditionalCache()

    def baixar_ano(self: "CvmMonthlyDownloader", ano: int) -> bytes:
        """Retorna o ZIP anual, revalidando a fonte antes de reutilizá-lo."""
        resultado = self._conditional.get_file_or_revalidate(
            self._zip_path(ano),
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

    def _obter(self: "CvmMonthlyDownloader", ano: int) -> tuple[bytes, Mapping[str, str]]:
        """Obtém o arquivo e os validadores, tolerando loaders que devolvem bytes."""
        resultado = self._fetch(ano)
        if isinstance(resultado, tuple):
            return resultado
        return resultado, {}

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

    def _persistir(
        self: "CvmMonthlyDownloader",
        ano: int,
        data: bytes,
        validators: Mapping[str, str] | None = None,
        revalidated_at: datetime | None = None,
    ) -> None:
        """Grava o ZIP bruto, o hash e os metadados do ano."""
        diretorio = self._base / str(ano)
        diretorio.mkdir(parents=True, exist_ok=True)
        (diretorio / f"inf_mensal_fii_{ano}.zip").write_bytes(data)
        digest = hash_sha256(data)
        (diretorio / "SHA256").write_text(digest, encoding="utf-8")
        anterior = self._ler_metadados(ano)
        agora = datetime.now(timezone.utc)
        baixado_em = (
            anterior.get("downloaded_at")
            if anterior and anterior.get("sha256") == digest
            else agora.isoformat()
        )
        metadata = {
            "dataset": "FII-INF-MENSAL",
            "year": ano,
            "url": url_anual(ano),
            "downloaded_at": baixado_em,
            "sha256": digest,
            "parser_version": self._parser_version,
            **(validators or {}),
            "revalidated_at": (revalidated_at or agora).isoformat(),
        }
        (diretorio / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

    def _baixar_http(
        self: "CvmMonthlyDownloader", ano: int
    ) -> tuple[bytes, Mapping[str, str]]:
        """Baixa o ZIP anual via HTTP, devolvendo validadores remotos."""
        url = url_anual(ano)
        logger.info("Baixando informe mensal CVM via %s", url)
        resposta = self._session.get(url, timeout=60)
        resposta.raise_for_status()
        return resposta.content, headers_to_validators(resposta.headers)

    def _probe_http(
        self: "CvmMonthlyDownloader", ano: int, validators: Mapping[str, str]
    ) -> RevalidationResult:
        """Verifica a fonte remota por HEAD, com fallback para GET condicional."""
        url = url_anual(ano)
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
        self: "CvmMonthlyDownloader", ano: int
    ) -> dict[str, object] | None:
        """Lê os metadados do ano, ou ``None`` quando ausentes/corrompidos."""
        caminho = self._base / str(ano) / "metadata.json"
        if not caminho.exists():
            return None
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return dados if isinstance(dados, dict) else None

    def _ler_validadores(self: "CvmMonthlyDownloader", ano: int) -> dict[str, str]:
        """Retorna os validadores remotos registrados para o ano."""
        dados = self._ler_metadados(ano) or {}
        return {
            chave: str(dados[chave])
            for chave in ("etag", "last_modified", "content_length", "revalidated_at")
            if dados.get(chave)
        }

    def _zip_path(self: "CvmMonthlyDownloader", ano: int) -> Path:
        """Retorna o caminho local do ZIP anual."""
        return self._base / str(ano) / f"inf_mensal_fii_{ano}.zip"
