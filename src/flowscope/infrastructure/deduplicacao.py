"""Housekeeping e poda da deduplicação por hash de conteúdo.

Varre os arquivos em cache sem hash — documentos de um ticker e notícias em
escopo global — na ordem cronológica e aplica a mesma regra do download:
duplicatas exatas são removidas junto com os seus derivados (resumo, texto e,
para notícias, a entrada do índice). A leitura e a remoção são tolerantes a
falhas isoladas por arquivo.
"""

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from flowscope.application.cancellation import CancellationToken
from flowscope.application.deduplicacao import conteudo_hashavel, eh_duplicata
from flowscope.infrastructure.b3.noticias_aquisicao import ESCOPO_NOTICIAS
from flowscope.infrastructure.b3.noticias_index import NoticiasIndexStore
from flowscope.infrastructure.b3.noticias_shards import (
    NoticiasSummaryStore,
    NoticiasTextStore,
)
from flowscope.infrastructure.content_hashes import (
    JsonHashStore,
    caminho_hashes_documentos,
    caminho_hashes_noticias,
    hash_sha256,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore

logger = logging.getLogger("flowscope")

#: Subpastas de documento sob a raiz de cache e o padrão de varredura.
_PASTAS_DOCUMENTOS: tuple[tuple[str, str], ...] = (
    ("bdr", "*/*/*.pdf"),
    ("informe-mensal", "*/*/*.html"),
    ("documentos-relevantes", "*/*/*/*.pdf"),
)

#: Subpasta das notícias e o padrão de varredura do HTML do corpo.
_PASTA_NOTICIAS = "noticias"
_PADRAO_NOTICIAS = "*/*/*.html"


@dataclass(frozen=True)
class CandidatoHash:
    """Arquivo candidato ao housekeeping, com a sua ordem cronológica."""

    relativo: str
    caminho: Path
    ordem: tuple


class PodadorDerivados(Protocol):
    """Contrato de remoção do arquivo e dos seus registros derivados."""

    def __call__(self: "PodadorDerivados", relativo: str) -> None:
        """Remove o arquivo e os derivados do caminho relativo."""
        ...


def podar_documento(cache_root: Path, ticker: str, relativo: str) -> None:
    """Remove um documento e os seus resumos e textos do ticker."""
    root = Path(cache_root)
    (root / relativo).unlink(missing_ok=True)
    JsonDocumentSummaryStore(root).remover(ticker, relativo)
    JsonDocumentTextStore(root).remover(ticker, relativo)


def podar_noticia(cache_root: Path, relativo: str) -> None:
    """Remove uma notícia, a sua entrada de índice e os seus resumos e textos."""
    root = Path(cache_root)
    (root / relativo).unlink(missing_ok=True)
    NoticiasIndexStore(root).remover(relativo)
    NoticiasSummaryStore(root).remover(ESCOPO_NOTICIAS, relativo)
    NoticiasTextStore(root).remover(ESCOPO_NOTICIAS, relativo)


def candidatos_documentos(cache_root: Path, ticker: str) -> list[CandidatoHash]:
    """Lista os documentos do ticker em ordem cronológica (mais antigo antes)."""
    root = Path(cache_root)
    pasta_ticker = ticker.strip().upper()
    candidatos: list[CandidatoHash] = []
    for pasta, padrao in _PASTAS_DOCUMENTOS:
        base = root / pasta / pasta_ticker
        for caminho in base.glob(padrao):
            if not caminho.is_file():
                continue
            relativo = caminho.relative_to(root).as_posix()
            candidatos.append(
                CandidatoHash(relativo, caminho, _ordem(caminho, root))
            )
    candidatos.sort(key=lambda candidato: candidato.ordem)
    return candidatos


def candidatos_noticias(cache_root: Path) -> list[CandidatoHash]:
    """Lista as notícias em cache em ordem cronológica (mais antiga antes)."""
    root = Path(cache_root)
    base = root / _PASTA_NOTICIAS
    candidatos: list[CandidatoHash] = []
    for caminho in base.glob(_PADRAO_NOTICIAS):
        if not caminho.is_file():
            continue
        relativo = caminho.relative_to(root).as_posix()
        candidatos.append(
            CandidatoHash(relativo, caminho, _ordem(caminho, root))
        )
    candidatos.sort(key=lambda candidato: candidato.ordem)
    return candidatos


class HousekeepingDeduplicacao:
    """Aplica a deduplicação aos arquivos em cache que ainda não têm hash."""

    def __init__(
        self: "HousekeepingDeduplicacao",
        cache_root: Path,
        registry: JsonHashStore,
        podar: PodadorDerivados,
    ) -> None:
        """Inicializa o housekeeping com a raiz, o registro e a poda."""
        self._root = Path(cache_root)
        self._registry = registry
        self._podar = podar

    def executar(
        self: "HousekeepingDeduplicacao",
        candidatos: Iterable[CandidatoHash],
        cancel_token: CancellationToken | None = None,
    ) -> None:
        """Percorre os candidatos, registrando hashes e removendo duplicatas."""
        self._limpar_invalidos()
        registrados = self._registry.registrados()
        canonicos = set(registrados.values())
        for candidato in candidatos:
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()
            if candidato.relativo in canonicos:
                continue
            digest = self._hash_do_candidato(candidato)
            if digest is None:
                continue
            canonico = registrados.get(digest)
            if eh_duplicata(
                digest, canonico, self._existe(canonico), candidato.relativo
            ):
                self._remover_duplicata(candidato.relativo)
                continue
            if canonico is not None:
                self._registry.remover(digest)
            self._registry.registrar(digest, candidato.relativo)
            registrados[digest] = candidato.relativo
            canonicos.add(candidato.relativo)

    def _hash_do_candidato(
        self: "HousekeepingDeduplicacao", candidato: CandidatoHash
    ) -> str | None:
        """Calcula o hash do conteúdo, tolerando falha de leitura."""
        try:
            conteudo = candidato.caminho.read_bytes()
        except OSError:
            logger.warning(
                "Falha ao ler %s para hash", candidato.relativo, exc_info=True
            )
            return None
        if not conteudo_hashavel(conteudo):
            return None
        return hash_sha256(conteudo)

    def _remover_duplicata(
        self: "HousekeepingDeduplicacao", relativo: str
    ) -> None:
        """Remove o arquivo duplicado e os seus derivados, tolerando falha."""
        try:
            self._podar(relativo)
        except OSError:
            logger.warning(
                "Falha ao remover duplicata %s", relativo, exc_info=True
            )

    def _existe(
        self: "HousekeepingDeduplicacao", canonico: str | None
    ) -> bool:
        """Indica se o arquivo canônico existe no disco."""
        return canonico is not None and (self._root / canonico).is_file()

    def _limpar_invalidos(self: "HousekeepingDeduplicacao") -> None:
        """Remove do registro entradas cujo arquivo canônico desapareceu."""
        for digest, relativo in list(self._registry.registrados().items()):
            if not (self._root / relativo).is_file():
                self._registry.remover(digest)


def executar_housekeeping_documentos(
    cache_root: Path,
    ticker: str,
    cancel_token: CancellationToken | None = None,
) -> None:
    """Executa o housekeeping dos documentos de um ticker."""
    root = Path(cache_root)
    registry = JsonHashStore(caminho_hashes_documentos(root, ticker))
    housekeeping = HousekeepingDeduplicacao(
        root, registry, lambda relativo: podar_documento(root, ticker, relativo)
    )
    housekeeping.executar(candidatos_documentos(root, ticker), cancel_token)


def executar_housekeeping_noticias(
    cache_root: Path,
    cancel_token: CancellationToken | None = None,
) -> None:
    """Executa o housekeeping global das notícias."""
    root = Path(cache_root)
    registry = JsonHashStore(caminho_hashes_noticias(root))
    housekeeping = HousekeepingDeduplicacao(
        root, registry, lambda relativo: podar_noticia(root, relativo)
    )
    housekeeping.executar(candidatos_noticias(root), cancel_token)


def _ordem(caminho: Path, root: Path) -> tuple:
    """Deriva a chave cronológica ``(ano, mês, nome)`` do caminho."""
    try:
        partes = caminho.relative_to(root).parts
    except ValueError:
        partes = caminho.parts
    ano, mes = _ano_mes(partes)
    return (ano, mes, caminho.name)


def _ano_mes(partes: tuple[str, ...]) -> tuple[int, int]:
    """Extrai ``(ano, mês)`` do primeiro par numérico ``AAAA/MM`` do caminho."""
    for indice, parte in enumerate(partes):
        if not (parte.isdigit() and len(parte) == 4):
            continue
        if indice + 1 < len(partes) and partes[indice + 1].isdigit():
            return int(parte), int(partes[indice + 1])
    return 0, 0
