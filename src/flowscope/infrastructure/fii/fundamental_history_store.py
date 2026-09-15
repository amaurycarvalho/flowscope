"""Cache histórico em disco dos resultados da análise fundamentalista.

Mantém, por ticker, um mapa ``data -> observação`` em JSON, com retenção
deslizante de 365 dias, escrita atômica e tolerância a corrupção. Serve o
read-through do caso de uso e a recuperação da evolução do ticker.
"""

import json
import logging
import re
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flowscope.application.fundamental_ports import (
    SCHEMA_VERSION_FUNDAMENTOS,
    ObservacaoFundamental,
    observacao_completa,
)
from flowscope.domain.fii import AnaliseFundamental
from flowscope.infrastructure.cache import CacheManager
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

from .fundamental_analysis_codec import analise_de_dict, analise_para_dict

logger = logging.getLogger("flowscope")

#: Subdiretório padrão do cache histórico dentro do diretório de cache.
DIRETORIO_HISTORICO = "fundamentos"

#: Retenção padrão das observações, em dias.
RETENCAO_PADRAO_DIAS = 365

#: Padrão de caracteres seguros para compor o nome do arquivo por ticker.
_CARACTERES_INSEGUROS = re.compile(r"[^A-Za-z0-9._-]")


class JsonFundamentalHistoryStore:
    """Armazena observações datadas por ticker em arquivos JSON."""

    def __init__(
        self: "JsonFundamentalHistoryStore",
        cache_dir: Path | None = None,
        now: Callable[[], datetime] | None = None,
        schema_version: int = SCHEMA_VERSION_FUNDAMENTOS,
        retention_days: int = RETENCAO_PADRAO_DIAS,
    ) -> None:
        """Inicializa o store com o diretório, o relógio e a política de retenção."""
        base = cache_dir if cache_dir is not None else CacheManager().get_cache_dir()
        self._cache_dir = Path(base) / DIRETORIO_HISTORICO
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._schema_version = schema_version
        self._retention = timedelta(days=retention_days)

    def obter(
        self: "JsonFundamentalHistoryStore", ticker: str, data: date
    ) -> AnaliseFundamental | None:
        """Retorna a observação da data, apenas na versão de schema atual."""
        if self._expirada(data):
            return None
        registro = self._carregar(ticker).get(data.isoformat())
        if registro is None:
            return None
        if registro.get("schema_version") != self._schema_version:
            return None
        return self._analise_do_registro(registro)

    def historico(
        self: "JsonFundamentalHistoryStore", ticker: str, inicio: date, fim: date
    ) -> list[ObservacaoFundamental]:
        """Retorna as observações do intervalo, tolerando versões antigas."""
        limite = self._limite()
        observacoes = self._carregar(ticker)
        resultado: list[ObservacaoFundamental] = []
        for chave, registro in observacoes.items():
            momento = _data_de_chave(chave)
            if momento is None or momento < limite or not (inicio <= momento <= fim):
                continue
            analise = self._analise_do_registro(registro)
            if analise is None:
                continue
            resultado.append(
                ObservacaoFundamental(
                    ticker=ticker.strip().upper(),
                    data=momento,
                    analise=analise,
                    schema_version=int(registro.get("schema_version") or 0),
                )
            )
        resultado.sort(key=lambda observacao: observacao.data)
        return resultado

    def datas(self: "JsonFundamentalHistoryStore", ticker: str) -> list[date]:
        """Retorna as datas com observação retida, em ordem crescente."""
        limite = self._limite()
        datas = [
            momento
            for chave in self._carregar(ticker)
            if (momento := _data_de_chave(chave)) is not None and momento >= limite
        ]
        return sorted(datas)

    def registrar(
        self: "JsonFundamentalHistoryStore",
        ticker: str,
        data: date,
        analise: AnaliseFundamental,
        *,
        force: bool = False,
    ) -> None:
        """Registra a observação, respeitando falhas e a política de parcialidade."""
        observacoes = self._purgar(self._carregar(ticker))
        chave = data.isoformat()
        existente = observacoes.get(chave)
        if existente is not None and not force and self._imutavel(existente):
            return
        observacoes[chave] = self._montar_registro(analise)
        self._gravar(ticker, observacoes)

    def _montar_registro(self: "JsonFundamentalHistoryStore", analise: AnaliseFundamental) -> dict:
        """Monta o registro persistido de uma observação."""
        return {
            "schema_version": self._schema_version,
            "completa": observacao_completa(analise),
            "fetched_at": self._now().isoformat(),
            "analise": analise_para_dict(analise),
        }

    def _imutavel(self: "JsonFundamentalHistoryStore", registro: dict) -> bool:
        """Indica se o registro é completo e está na versão atual do schema."""
        return (
            registro.get("schema_version") == self._schema_version
            and bool(registro.get("completa"))
        )

    def _analise_do_registro(
        self: "JsonFundamentalHistoryStore", registro: dict
    ) -> AnaliseFundamental | None:
        """Desserializa a análise de um registro, tolerando registros inválidos."""
        analise = registro.get("analise")
        if not isinstance(analise, dict):
            return None
        try:
            return analise_de_dict(analise)
        except (KeyError, TypeError, ValueError):
            return None

    def _expirada(self: "JsonFundamentalHistoryStore", data: date) -> bool:
        """Indica se a data está fora da janela de retenção."""
        return data < self._limite()

    def _limite(self: "JsonFundamentalHistoryStore") -> date:
        """Retorna a data-limite da janela de retenção."""
        return self._now().date() - self._retention

    def _purgar(self: "JsonFundamentalHistoryStore", observacoes: dict) -> dict:
        """Descarta observações fora da janela de retenção."""
        limite = self._limite()
        return {
            chave: registro
            for chave, registro in observacoes.items()
            if (momento := _data_de_chave(chave)) is not None and momento >= limite
        }

    def _carregar(self: "JsonFundamentalHistoryStore", ticker: str) -> dict:
        """Carrega o mapa de observações do ticker, tolerando ausência/corrupção."""
        caminho = self._path_for(ticker)
        if not caminho.exists():
            return {}
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Histórico fundamental corrompido: %s", caminho)
            return {}
        if not isinstance(dados, dict):
            return {}
        observacoes = dados.get("observacoes")
        return observacoes if isinstance(observacoes, dict) else {}

    def _gravar(self: "JsonFundamentalHistoryStore", ticker: str, observacoes: dict) -> None:
        """Grava o mapa de observações de forma atômica."""
        payload = json.dumps(
            {"observacoes": observacoes}, ensure_ascii=False, default=str
        ).encode("utf-8")
        _atomic_write_bytes(self._path_for(ticker), payload)

    def _path_for(self: "JsonFundamentalHistoryStore", ticker: str) -> Path:
        """Resolve o caminho do arquivo de um ticker."""
        seguro = _CARACTERES_INSEGUROS.sub("_", ticker.strip().upper())
        return self._cache_dir / f"{seguro}.json"


def _data_de_chave(chave: object) -> date | None:
    """Interpreta a chave ``YYYY-MM-DD`` como ``date``, ou ``None``."""
    if not isinstance(chave, str):
        return None
    try:
        return date.fromisoformat(chave)
    except ValueError:
        return None
