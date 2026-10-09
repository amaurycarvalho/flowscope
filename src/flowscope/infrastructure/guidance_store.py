"""Ledger do guidance de distribuição por FII em JSON.

Cada FII tem um arquivo em ``~/.cache/flowscope/guidance/`` com uma entrada por
Relatório Gerencial avaliado, identificada pela chave de conteúdo do documento
(hash SHA-256, ou caminho relativo como fallback). Cada entrada guarda o método
de avaliação, a data do relatório, o caminho do PDF e o resultado (o guidance ou
a ausência avaliada). A leitura tolera arquivo ausente, corrompido ou no formato
v1 — este último é lido como uma entrada determinística — e a gravação é atômica
e serializada por lock. O guidance corrente é derivado da entrada com maior data
de relatório entre as que possuem guidance.
"""

import json
import logging
import re
import threading
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flowscope.domain.fii.guidance import (
    METODO_DETERMINISTICO,
    AvaliacaoGuidance,
    Guidance,
)
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

logger = logging.getLogger("flowscope")

#: Subdiretório do guidance dentro do diretório de cache.
DIRETORIO_GUIDANCE = "guidance"

#: Versão do schema persistido.
SCHEMA_VERSION_GUIDANCE = 2

#: Chave da entrada migrada do formato v1 (guidance único, sem hash nem origem).
CHAVE_LEGADA = "legacy"

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


class JsonGuidanceStore:
    """Armazena o ledger de avaliações por FII em JSON com escrita atômica."""

    def __init__(
        self: "JsonGuidanceStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o store no subdiretório de guidance do cache informado."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_GUIDANCE
        self._lock = threading.Lock()

    def obter(self: "JsonGuidanceStore", ticker: str) -> Guidance | None:
        """Retorna o guidance corrente derivado, ou ``None`` quando ausente."""
        return _corrente(self._entradas(ticker))

    def obter_avaliacao(
        self: "JsonGuidanceStore", ticker: str, chave: str
    ) -> AvaliacaoGuidance | None:
        """Retorna a avaliação do RG identificado por ``chave``, ou ``None``."""
        return self._entradas(ticker).get(chave)

    def avaliacoes(
        self: "JsonGuidanceStore", ticker: str
    ) -> dict[str, AvaliacaoGuidance]:
        """Retorna uma cópia do mapa de avaliações do ticker, por chave."""
        return dict(self._entradas(ticker))

    def salvar_avaliacao(
        self: "JsonGuidanceStore",
        ticker: str,
        chave: str,
        avaliacao: AvaliacaoGuidance,
    ) -> None:
        """Grava a avaliação do RG, substituindo a anterior da mesma chave."""
        with self._lock:
            entradas = self._entradas(ticker)
            entradas[chave] = avaliacao
            self._gravar(ticker, entradas)

    def _entradas(self: "JsonGuidanceStore", ticker: str) -> dict:
        """Carrega as entradas do ticker, migrando o formato v1 se necessário."""
        dados = self._carregar(ticker)
        if dados.get("schema_version") == SCHEMA_VERSION_GUIDANCE:
            return _entradas_de(dados.get("avaliacoes"))
        return _entradas_legadas(dados)

    def _carregar(self: "JsonGuidanceStore", ticker: str) -> dict:
        """Carrega o documento do ticker, tolerando ausência e corrupção."""
        caminho = self._path_for(ticker)
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Guidance corrompido: %s", caminho)
            return {}
        return dados if isinstance(dados, dict) else {}

    def _gravar(self: "JsonGuidanceStore", ticker: str, entradas: dict) -> None:
        """Grava o ledger do ticker de forma atômica no schema atual."""
        payload = json.dumps(
            {
                "schema_version": SCHEMA_VERSION_GUIDANCE,
                "avaliacoes": {
                    chave: _avaliacao_para_dict(avaliacao)
                    for chave, avaliacao in entradas.items()
                },
            },
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
        _atomic_write_bytes(self._path_for(ticker), payload)

    def _path_for(self: "JsonGuidanceStore", ticker: str) -> Path:
        """Resolve o caminho do arquivo de guidance de um ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"


def _corrente(entradas: dict[str, AvaliacaoGuidance]) -> Guidance | None:
    """Deriva o guidance corrente: maior data de relatório entre as entradas."""
    com_guidance = [
        avaliacao for avaliacao in entradas.values() if avaliacao.guidance is not None
    ]
    if not com_guidance:
        return None
    mais_recente = max(com_guidance, key=lambda a: a.data_relatorio)
    return mais_recente.guidance


def _entradas_de(dados: object) -> dict[str, AvaliacaoGuidance]:
    """Reconstrói o mapa de entradas, descartando registros inválidos."""
    if not isinstance(dados, dict):
        return {}
    entradas: dict[str, AvaliacaoGuidance] = {}
    for chave, valor in dados.items():
        if not isinstance(chave, str):
            continue
        avaliacao = _para_avaliacao(valor)
        if avaliacao is not None:
            entradas[chave] = avaliacao
    return entradas


def _entradas_legadas(dados: dict) -> dict[str, AvaliacaoGuidance]:
    """Lê o formato v1 (guidance único) como entrada determinística."""
    guidance = _para_guidance(dados.get("guidance"))
    if guidance is None:
        return {}
    return {
        CHAVE_LEGADA: AvaliacaoGuidance(
            metodo=METODO_DETERMINISTICO,
            data_relatorio=guidance.data_relatorio,
            caminho_pdf=guidance.caminho_pdf,
            guidance=guidance,
        )
    }


def _avaliacao_para_dict(avaliacao: AvaliacaoGuidance) -> dict:
    """Serializa uma avaliação preservando a precisão, a data e o resultado."""
    return {
        "metodo": avaliacao.metodo,
        "data_relatorio": avaliacao.data_relatorio.isoformat(),
        "caminho_pdf": avaliacao.caminho_pdf,
        "guidance": (
            _guidance_para_dict(avaliacao.guidance)
            if avaliacao.guidance is not None
            else None
        ),
    }


def _guidance_para_dict(guidance: Guidance) -> dict:
    """Serializa o resultado de guidance (valor, faixa e período)."""
    return {
        "valor_min": str(guidance.valor_min),
        "valor_max": str(guidance.valor_max),
        "periodo": guidance.periodo,
    }


def _para_avaliacao(dados: object) -> AvaliacaoGuidance | None:
    """Reconstrói uma avaliação de um registro, ou ``None`` quando inválido."""
    if not isinstance(dados, dict):
        return None
    data_relatorio = _data_de(dados.get("data_relatorio"))
    if data_relatorio is None:
        return None
    metodo = dados.get("metodo")
    caminho = dados.get("caminho_pdf")
    bruto = dados.get("guidance")
    if bruto is None:
        guidance = None
    elif isinstance(bruto, dict):
        guidance = _para_guidance_resultado(bruto, data_relatorio, caminho)
        if guidance is None:
            return None
    else:
        return None
    return AvaliacaoGuidance(
        metodo=metodo if isinstance(metodo, str) and metodo else METODO_DETERMINISTICO,
        data_relatorio=data_relatorio,
        caminho_pdf=caminho if isinstance(caminho, str) else None,
        guidance=guidance,
    )


def _para_guidance_resultado(
    dados: dict, data_relatorio: date, caminho_pdf: object
) -> Guidance | None:
    """Reconstrói o guidance de um resultado, ou ``None`` quando inválido."""
    valor_min = _decimal_de(dados.get("valor_min"))
    valor_max = _decimal_de(dados.get("valor_max"))
    if valor_min is None or valor_max is None:
        return None
    periodo = dados.get("periodo")
    return Guidance(
        valor_min=valor_min,
        valor_max=valor_max,
        periodo=periodo if isinstance(periodo, str) else "",
        data_relatorio=data_relatorio,
        caminho_pdf=caminho_pdf if isinstance(caminho_pdf, str) else None,
    )


def _para_guidance(dados: object) -> Guidance | None:
    """Reconstrói um ``Guidance`` do formato v1, ou ``None`` quando inválido."""
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
