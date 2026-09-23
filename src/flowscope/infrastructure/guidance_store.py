"""Persistência do guidance de distribuição por FII em JSON.

Cada FII tem um arquivo em ``~/.cache/flowscope/guidance/`` com o último
guidance conhecido (valor mínimo/máximo por cota, período, data do relatório e
caminho do PDF). A leitura tolera arquivo ausente ou corrompido — tratado como
ausência de guidance — e a gravação é atômica.
"""

import json
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flowscope.domain.fii.guidance import Guidance
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório do guidance dentro do diretório de cache.
DIRETORIO_GUIDANCE = "guidance"

#: Versão do schema persistido.
SCHEMA_VERSION_GUIDANCE = 1

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


class JsonGuidanceStore:
    """Armazena o guidance por FII em JSON com escrita atômica."""

    def __init__(
        self: "JsonGuidanceStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no subdiretório de guidance do cache informado."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_GUIDANCE

    def obter(self: "JsonGuidanceStore", ticker: str) -> Guidance | None:
        """Retorna o guidance do ticker, ou ``None`` quando ausente/corrompido."""
        dados = self._carregar(ticker)
        return _para_guidance(dados.get("guidance"))

    def salvar(self: "JsonGuidanceStore", ticker: str, guidance: Guidance) -> None:
        """Grava o guidance do ticker, substituindo o anterior."""
        payload = json.dumps(
            {
                "schema_version": SCHEMA_VERSION_GUIDANCE,
                "guidance": _guidance_para_dict(guidance),
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        _atomic_write_bytes(self._path_for(ticker), payload)

    def _carregar(self: "JsonGuidanceStore", ticker: str) -> dict:
        """Carrega o registro do ticker, tolerando ausência e corrupção."""
        caminho = self._path_for(ticker)
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Guidance corrompido: %s", caminho)
            return {}
        return dados if isinstance(dados, dict) else {}

    def _path_for(self: "JsonGuidanceStore", ticker: str) -> Path:
        """Resolve o caminho do arquivo de guidance de um ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"


def _guidance_para_dict(guidance: Guidance) -> dict:
    """Serializa um ``Guidance`` preservando a precisão e a data."""
    return {
        "valor_min": str(guidance.valor_min),
        "valor_max": str(guidance.valor_max),
        "periodo": guidance.periodo,
        "data_relatorio": guidance.data_relatorio.isoformat(),
        "caminho_pdf": guidance.caminho_pdf,
    }


def _para_guidance(dados: object) -> Guidance | None:
    """Reconstrói um ``Guidance`` de um registro, ou ``None`` quando inválido."""
    if not isinstance(dados, dict):
        return None
    valor_min = _decimal_de(dados.get("valor_min"))
    valor_max = _decimal_de(dados.get("valor_max"))
    data_relatorio = _data_de(dados.get("data_relatorio"))
    if valor_min is None or valor_max is None or data_relatorio is None:
        return None
    periodo = dados.get("periodo")
    caminho = dados.get("caminho_pdf")
    return Guidance(
        valor_min=valor_min,
        valor_max=valor_max,
        periodo=periodo if isinstance(periodo, str) else "",
        data_relatorio=data_relatorio,
        caminho_pdf=caminho if isinstance(caminho, str) else None,
    )


def _decimal_de(valor: object) -> Decimal | None:
    """Retorna o ``Decimal`` de um valor persistido, ou ``None``."""
    if valor is None:
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return None


def _data_de(valor: object) -> date | None:
    """Retorna a ``date`` de uma data ISO persistida, ou ``None``."""
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError:
        return None
