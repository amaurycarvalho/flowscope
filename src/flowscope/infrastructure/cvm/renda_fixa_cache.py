"""Cache JSON por ticker dos títulos de renda fixa.

O arquivo fica em ``<cache>/direitos-obrigacoes/<TICKER>.json`` e é escrito
atomicamente. A leitura tolera JSON corrompido ou incompatível, devolvendo
``None`` sem derrubar a árvore.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from flowscope.application.renda_fixa.serializacao import (
    carteira_de_dict,
    carteira_para_dict,
)
from flowscope.domain.renda_fixa import CarteiraTitulos
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório de cache do ramo de direitos e obrigações.
SUBDIR = "direitos-obrigacoes"

_TICKER_VALIDO = re.compile(r"^[A-Z0-9._-]+$")


class RepositorioTitulosJson:
    """Persistência atômica e leitura tolerante da carteira por ticker."""

    def __init__(
        self: RepositorioTitulosJson, cache_dir: Path | None = None
    ) -> None:
        """Inicializa a raiz de cache, usando o padrão do sistema quando omitida."""
        base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
        self._base = base / SUBDIR

    def caminho(self: RepositorioTitulosJson, ticker: str) -> Path:
        """Retorna o caminho do cache do ticker, validando o identificador."""
        chave = (ticker or "").strip().upper()
        if not chave or not _TICKER_VALIDO.match(chave):
            raise ValueError(f"ticker inválido para cache de títulos: {ticker!r}")
        return self._base / f"{chave}.json"

    def ler(self: RepositorioTitulosJson, ticker: str) -> CarteiraTitulos | None:
        """Lê a carteira do ticker, ou ``None`` quando ausente/corrompida."""
        try:
            caminho = self.caminho(ticker)
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(dados, dict):
            return None
        try:
            return carteira_de_dict(dados)
        except (TypeError, ValueError):
            logger.warning(
                "Cache de títulos inválido para %s", ticker, exc_info=True
            )
            return None

    def gravar(
        self: RepositorioTitulosJson, carteira: CarteiraTitulos
    ) -> None:
        """Grava a carteira atomicamente no caminho por ticker."""
        caminho = self.caminho(carteira.ticker)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            carteira_para_dict(carteira), ensure_ascii=False, indent=2
        )
        _atomic_write_bytes(caminho, payload.encode("utf-8"))
