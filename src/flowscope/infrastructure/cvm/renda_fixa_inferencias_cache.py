"""Cache JSON por ticker das inferências de direitos e obrigações.

O arquivo fica em ``<cache>/direitos-obrigacoes/inferencias/<TICKER>.json``,
separado do cache oficial, e é escrito atomicamente. A leitura tolera JSON
corrompido ou incompatível, devolvendo ``None`` sem derrubar a árvore.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from flowscope.application.renda_fixa.serializacao_inferencias import (
    carteira_inferencias_de_dict,
    carteira_inferencias_para_dict,
)
from flowscope.domain.renda_fixa import CarteiraInferencias
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório das inferências dentro do ramo de direitos e obrigações.
SUBDIR = "inferencias"

_TICKER_VALIDO = re.compile(r"^[A-Z0-9._-]+$")


class RepositorioInferenciasJson:
    """Persistência atômica e leitura tolerante das inferências por ticker."""

    def __init__(
        self: RepositorioInferenciasJson, cache_dir: Path | None = None
    ) -> None:
        """Inicializa a raiz de cache, usando o padrão do sistema quando omitida."""
        base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
        self._base = base / "direitos-obrigacoes" / SUBDIR

    def caminho(self: RepositorioInferenciasJson, ticker: str) -> Path:
        """Retorna o caminho do cache do ticker, validando o identificador."""
        chave = (ticker or "").strip().upper()
        if not chave or not _TICKER_VALIDO.match(chave):
            raise ValueError(f"ticker inválido para cache de inferências: {ticker!r}")
        return self._base / f"{chave}.json"

    def ler(self: RepositorioInferenciasJson, ticker: str) -> CarteiraInferencias | None:
        """Lê as inferências do ticker, ou ``None`` quando ausentes/corrompidas."""
        try:
            caminho = self.caminho(ticker)
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        if not isinstance(dados, dict):
            return None
        try:
            return carteira_inferencias_de_dict(dados)
        except (TypeError, ValueError):
            logger.warning(
                "Cache de inferências inválido para %s", ticker, exc_info=True
            )
            return None

    def gravar(
        self: RepositorioInferenciasJson, carteira: CarteiraInferencias
    ) -> None:
        """Grava as inferências atomicamente no caminho por ticker."""
        caminho = self.caminho(carteira.ticker)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            carteira_inferencias_para_dict(carteira), ensure_ascii=False, indent=2
        )
        _atomic_write_bytes(caminho, payload.encode("utf-8"))
