"""Leitura e registro da data de referência dos fundamentos em ``config.json``.

Registra o marcador ``last_fundamentals`` (``{data, fetched_at}``) ao concluir
uma carga de fundamentos e resolve a data de referência consultada com fallback
para ``last_date``. A gravação é *read-modify-write*, atômica e sob o lock
global de ação, preservando os demais blocos do arquivo.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from flowscope.infrastructure.action_lock import ActionLock, OperacaoEmAndamento

logger = logging.getLogger("flowscope")

#: Chave do marcador da última carga de fundamentos.
CHAVE_MARCADOR = "last_fundamentals"

#: Espera máxima, em segundos, para adquirir o lock ao gravar o marcador.
_ESPERA_LOCK = 5.0


def _config_path(path: Path | None = None) -> Path:
    """Resolve o caminho do ``config.json`` a usar."""
    if path is not None:
        return Path(path)
    from flowscope.infrastructure.llm.config import CONFIG_PATH

    return CONFIG_PATH


def carregar_config(path: Path | None = None) -> dict:
    """Lê o ``config.json`` como dicionário, devolvendo vazio em falha."""
    caminho = _config_path(path)
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dados if isinstance(dados, dict) else {}


def _parse_data(valor: object) -> date | None:
    """Interpreta uma data ISO (``AAAA-MM-DD``), ou ``None``."""
    if isinstance(valor, date):
        return valor
    if not isinstance(valor, str) or not valor:
        return None
    try:
        return date.fromisoformat(valor[:10])
    except ValueError:
        return None


def resolver_data_referencia(path: Path | None = None) -> date | None:
    """Resolve a data de referência: ``last_fundamentals.data`` → ``last_date``.

    É o único ponto de verdade reusado pelo nó da árvore, pela operação do
    núcleo, pela tool MCP e pelo comando ``nav``. Sem nenhum dos dois valores,
    devolve ``None`` (ausência de data, sem erro).
    """
    dados = carregar_config(path)
    marcador = dados.get(CHAVE_MARCADOR)
    if isinstance(marcador, dict):
        data = _parse_data(marcador.get("data"))
        if data is not None:
            return data
    return _parse_data(dados.get("last_date"))


def registrar_last_fundamentals(
    data: date,
    *,
    fetched_at: datetime | None = None,
    path: Path | None = None,
) -> None:
    """Grava ``last_fundamentals`` preservando os demais blocos do arquivo.

    A gravação relê o arquivo, aplica apenas o marcador e grava de forma atômica
    sob o lock global de ação, de modo que uma carga concorrente não perca
    chaves como ``last_tickers`` ou ``llm``.
    """
    momento = fetched_at or datetime.now(timezone.utc)
    gravar_config(
        {
            CHAVE_MARCADOR: {
                "data": data.isoformat(),
                "fetched_at": momento.isoformat(),
            }
        },
        path=path,
    )


def gravar_config(chaves: dict, *, path: Path | None = None) -> None:
    """Aplica ``chaves`` ao ``config.json`` de forma atômica e sob o lock.

    Faz *read-modify-write*: relê o arquivo, sobrepõe as chaves informadas e
    grava de forma atômica sob o lock global de ação, preservando os demais
    blocos do arquivo.
    """
    from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

    caminho = _config_path(path)
    lock = ActionLock()
    try:
        lock.adquirir(esperar=_ESPERA_LOCK)
    except OperacaoEmAndamento:
        logger.warning(
            "Lock de ação indisponível ao gravar config; escrevendo atômico"
        )
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        dados = carregar_config(caminho)
        dados.update(chaves)
        _atomic_write_bytes(
            caminho, json.dumps(dados, indent=2, default=str).encode("utf-8")
        )
    except OSError:
        logger.warning("Falha ao gravar o config.json", exc_info=True)
    finally:
        lock.liberar()
