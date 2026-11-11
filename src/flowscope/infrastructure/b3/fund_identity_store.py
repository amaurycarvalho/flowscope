"""Persistência da identidade de fundos B3 por ticker.

Cada ticker tem um arquivo ``<cache>/fund_identity/<TICKER>.json`` com a
identidade resolvida na B3 (``idFNET``, CNPJ, nome e tipo). A leitura tolera
ausência, corrupção e versão de schema antiga; a escrita é atômica e o registro
não expira, já que o CNPJ de um fundo muda raramente.
"""

import json
import logging
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório da identidade de fundos dentro do diretório de cache.
DIRETORIO_IDENTIDADE = "fund_identity"

#: Versão do schema persistido.
SCHEMA_VERSION_IDENTIDADE = 1

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


@dataclass(frozen=True)
class FundIdentityRecord:
    """Identidade persistida de um fundo B3."""

    ticker: str
    id_fnet: str
    primary_id: str | None
    name: str
    trading_name: str | None
    cnpj: str | None
    type_fund: str | None
    updated_at: str


class JsonFundIdentityStore:
    """Armazena a identidade de cada ticker em um arquivo JSON próprio."""

    def __init__(
        self: "JsonFundIdentityStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no subdiretório de identidade do cache informado."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_IDENTIDADE
        self._lock = threading.Lock()

    def caminho(self: "JsonFundIdentityStore", ticker: str) -> Path:
        """Retorna o caminho do registro persistido do ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"

    def obter(self: "JsonFundIdentityStore", ticker: str) -> FundIdentityRecord | None:
        """Retorna a identidade persistida, ou ``None`` quando inválida/ausente."""
        caminho = self.caminho(ticker)
        if not caminho.exists():
            return None
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Identidade de fundo corrompida: %s", caminho)
            return None
        if not isinstance(dados, dict):
            return None
        if dados.get("schema_version") != SCHEMA_VERSION_IDENTIDADE:
            return None
        return _registro_de(dados, ticker)

    def salvar(
        self: "JsonFundIdentityStore",
        ticker: str,
        *,
        id_fnet: str,
        primary_id: str | None = None,
        name: str = "",
        trading_name: str | None = None,
        cnpj: str | None = None,
        type_fund: str | None = None,
    ) -> None:
        """Grava a identidade do ticker de forma atômica no schema atual."""
        registro = {
            "schema_version": SCHEMA_VERSION_IDENTIDADE,
            "ticker": ticker.strip().upper(),
            "id_fnet": str(id_fnet),
            "primary_id": str(primary_id) if primary_id is not None else None,
            "name": name,
            "trading_name": trading_name,
            "cnpj": cnpj,
            "type_fund": type_fund,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        payload = json.dumps(registro, ensure_ascii=False).encode("utf-8")
        with self._lock:
            _atomic_write_bytes(self.caminho(ticker), payload)

    def invalidar(self: "JsonFundIdentityStore", ticker: str) -> None:
        """Remove o registro persistido do ticker, se existir."""
        caminho = self.caminho(ticker)
        if caminho.exists():
            caminho.unlink()


def _registro_de(dados: dict, ticker: str) -> FundIdentityRecord | None:
    """Reconstrói o registro a partir do JSON, ou ``None`` quando incompleto."""
    id_fnet = dados.get("id_fnet")
    if id_fnet is None or not str(id_fnet):
        return None
    return FundIdentityRecord(
        ticker=str(dados.get("ticker") or ticker.strip().upper()),
        id_fnet=str(id_fnet),
        primary_id=(
            str(dados["primary_id"])
            if dados.get("primary_id") is not None
            else None
        ),
        name=str(dados.get("name") or ""),
        trading_name=(
            str(dados["trading_name"])
            if dados.get("trading_name") is not None
            else None
        ),
        cnpj=str(dados["cnpj"]) if dados.get("cnpj") is not None else None,
        type_fund=(
            str(dados["type_fund"])
            if dados.get("type_fund") is not None
            else None
        ),
        updated_at=str(dados.get("updated_at") or ""),
    )
