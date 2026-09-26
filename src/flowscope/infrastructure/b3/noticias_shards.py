"""Caches de notícias particionados por ano e mês.

As notícias são muitas e compartilham o escopo ``NOTICIAS`` nos stores JSON.
Para não reescrever um único arquivo a cada item (custo ~O(N²)), o escopo de
cache de cada notícia é o shard ``NOTICIAS-<ANO>-<MES>``, derivado da própria
chave estável (``noticias/<ANO>/<MES>/<hash>.html``). Os stores concretos de
texto e resumo são reaproveitados por subclasses que traduzem o escopo e
mesclam os shards na leitura em massa. O cache no formato anterior
(``NOTICIAS.json``) é migrado na primeira operação, sem reconverter arquivos.
"""

import logging
from pathlib import Path

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.infrastructure.b3.noticias_aquisicao import ESCOPO_NOTICIAS
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

logger = logging.getLogger("flowscope")

__all__ = [
    "ESCOPO_SEM_DATA",
    "NoticiasSummaryStore",
    "NoticiasTextStore",
    "escopo_shard",
]

#: Escopo de fallback para chaves fora do padrão ``noticias/<ano>/<mes>/...``.
ESCOPO_SEM_DATA = f"{ESCOPO_NOTICIAS}-SEM-DATA"

#: Prefixo da chave estável das notícias dentro da raiz de cache.
_PREFIXO_NOTICIAS = "noticias"


def escopo_shard(chave: str) -> str:
    """Deriva o shard ``NOTICIAS-<ANO>-<MES>`` da chave estável da notícia."""
    partes = Path(chave).parts
    if len(partes) >= 3 and partes[0] == _PREFIXO_NOTICIAS:
        ano, mes = partes[1], partes[2]
        if ano.isdigit() and mes.isdigit() and 1 <= int(mes) <= 12:
            return f"{ESCOPO_NOTICIAS}-{int(ano):04d}-{int(mes):02d}"
    return ESCOPO_SEM_DATA


def _escopo_de(ticker: str, chave: str) -> str:
    """Traduz o escopo base das notícias para o shard da chave."""
    if ticker == ESCOPO_NOTICIAS:
        return escopo_shard(chave)
    return ticker


def _shards(cache_dir: Path) -> list[str]:
    """Lista os escopos dos shards de notícias presentes no diretório."""
    if not cache_dir.is_dir():
        return []
    return sorted(
        arquivo.stem
        for arquivo in cache_dir.glob(f"{ESCOPO_NOTICIAS}-*.json")
    )


class NoticiasTextStore(JsonDocumentTextStore):
    """Cache de texto das notícias particionado por ano e mês."""

    def __init__(
        self: "NoticiasTextStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o cache de texto de notícias."""
        super().__init__(cache_dir=cache_dir)
        self._migrado = False

    def obter(self: "NoticiasTextStore", ticker: str, chave: str) -> str | None:
        """Retorna o texto da notícia a partir do seu shard."""
        self._garantir_migracao()
        return super().obter(_escopo_de(ticker, chave), chave)

    def salvar(
        self: "NoticiasTextStore", ticker: str, chave: str, texto: str
    ) -> None:
        """Grava o texto da notícia no seu shard."""
        self._garantir_migracao()
        super().salvar(_escopo_de(ticker, chave), chave, texto)

    def textos(self: "NoticiasTextStore", ticker: str) -> dict[str, str]:
        """Retorna os textos do escopo, mesclando os shards de notícias."""
        if ticker != ESCOPO_NOTICIAS:
            return super().textos(ticker)
        self._garantir_migracao()
        resultado: dict[str, str] = {}
        for escopo in _shards(self._cache_dir):
            resultado.update(super().textos(escopo))
        return resultado

    def _garantir_migracao(self: "NoticiasTextStore") -> None:
        """Migra o ``NOTICIAS.json`` anterior para os shards, uma única vez."""
        if self._migrado:
            return
        self._migrado = True
        legado = self._cache_dir / f"{ESCOPO_NOTICIAS}.json"
        if not legado.exists():
            return
        try:
            antigos = super().textos(ESCOPO_NOTICIAS)
            for chave, texto in antigos.items():
                super().salvar(escopo_shard(chave), chave, texto)
            legado.unlink(missing_ok=True)
        except OSError:
            logger.warning("Falha ao migrar textos de notícias", exc_info=True)


class NoticiasSummaryStore(JsonDocumentSummaryStore):
    """Cache de resumo das notícias particionado por ano e mês."""

    def __init__(
        self: "NoticiasSummaryStore", cache_dir: Path | None = None
    ) -> None:
        """Inicializa o cache de resumo de notícias."""
        super().__init__(cache_dir=cache_dir)
        self._migrado = False

    def obter(
        self: "NoticiasSummaryStore", ticker: str, chave: str
    ) -> ResumoDocumento | None:
        """Retorna o resumo da notícia a partir do seu shard."""
        self._garantir_migracao()
        return super().obter(_escopo_de(ticker, chave), chave)

    def salvar(
        self: "NoticiasSummaryStore",
        ticker: str,
        chave: str,
        short_summary: str,
        long_summary: str,
    ) -> None:
        """Grava o resumo da notícia no seu shard."""
        self._garantir_migracao()
        super().salvar(
            _escopo_de(ticker, chave), chave, short_summary, long_summary
        )

    def resumos(self: "NoticiasSummaryStore", ticker: str) -> dict:
        """Retorna os resumos do escopo, mesclando os shards de notícias."""
        if ticker != ESCOPO_NOTICIAS:
            return super().resumos(ticker)
        self._garantir_migracao()
        resultado: dict = {}
        for escopo in _shards(self._cache_dir):
            resultado.update(super().resumos(escopo))
        return resultado

    def _garantir_migracao(self: "NoticiasSummaryStore") -> None:
        """Migra o ``NOTICIAS.json`` anterior para os shards, uma única vez."""
        if self._migrado:
            return
        self._migrado = True
        legado = self._cache_dir / f"{ESCOPO_NOTICIAS}.json"
        if not legado.exists():
            return
        try:
            antigos = super().resumos(ESCOPO_NOTICIAS)
            for chave, resumo in antigos.items():
                super().salvar(
                    escopo_shard(chave),
                    chave,
                    resumo.short_summary,
                    resumo.long_summary,
                )
            legado.unlink(missing_ok=True)
        except OSError:
            logger.warning("Falha ao migrar resumos de notícias", exc_info=True)
