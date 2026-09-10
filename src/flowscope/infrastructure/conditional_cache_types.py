"""Tipos, protocolos e utilitários do cache condicional."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Protocol

#: Chaves de validação HTTP reconhecidas pelos validadores e metadados.
ETAG = "etag"
LAST_MODIFIED = "last_modified"
CONTENT_LENGTH = "content_length"
DATA_ULTIMA_COTACAO = "data_ultima_cotacao"
REVALIDATED_AT = "revalidated_at"

#: Políticas padrão do cache condicional.
_ZERO = timedelta(0)
_RETENTION_PADRAO = timedelta(days=30)


class RevalidationStatus(Enum):
    """Resultado da checagem de um validador contra a fonte remota."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    UNKNOWN = "unknown"


class CacheOutcome(Enum):
    """Resultado de uma consulta ao cache condicional."""

    HIT = "hit"
    REVALIDATED = "revalidated"
    UPDATED = "updated"
    MISS = "miss"


@dataclass(frozen=True)
class RevalidationResult:
    """Decisão de um validador e os validadores atualizados."""

    status: RevalidationStatus
    payload: object | None = None
    validators: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Fetched:
    """Conteúdo recém-obtido da fonte e os validadores que o acompanham."""

    payload: object
    validators: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheRecord:
    """Registro armazenado, com conteúdo, validadores e versão do parser."""

    payload: object
    validators: Mapping[str, str] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parser_version: str = ""


@dataclass(frozen=True)
class CacheResult:
    """Valor devolvido pelo cache e o resultado da consulta."""

    value: object
    outcome: CacheOutcome


@dataclass(frozen=True)
class FileCacheResult:
    """Arquivo devolvido pelo cache condicional de arquivos."""

    data: bytes
    outcome: CacheOutcome
    validators: Mapping[str, str] = field(default_factory=dict)


class RemoteResponse(Protocol):
    """Resposta mínima de uma requisição HTTP usada pelos validadores."""

    status_code: int
    text: str
    headers: Mapping[str, str]


class Validator(Protocol):
    """Contrato de um validador de cache."""

    def revalidate(self: Validator, record: CacheRecord) -> RevalidationResult:
        """Compara o registro armazenado com a fonte remota."""
        ...


def headers_to_validators(headers: Mapping[str, str]) -> dict[str, str]:
    """Extrai os validadores HTTP relevantes dos cabeçalhos de resposta."""
    validators: dict[str, str] = {}
    if headers.get("ETag"):
        validators[ETAG] = str(headers["ETag"])
    if headers.get("Last-Modified"):
        validators[LAST_MODIFIED] = str(headers["Last-Modified"])
    if headers.get("Content-Length"):
        validators[CONTENT_LENGTH] = str(headers["Content-Length"])
    return validators


def _parse_iso_date(valor: object) -> date | None:
    """Interpreta uma data ISO armazenada em validadores, ou ``None``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _parse_datetime(valor: object) -> datetime | None:
    """Interpreta um instante ISO, normalizando para UTC, ou ``None``."""
    if not valor:
        return None
    try:
        instante = datetime.fromisoformat(str(valor))
    except ValueError:
        return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(timezone.utc)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Grava bytes de forma atômica, com arquivo temporário e rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.rename(path)
