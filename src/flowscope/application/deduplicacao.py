"""Política pura e portas da deduplicação de conteúdo por hash.

A decisão de manter ou descartar um arquivo baixado é isolada do I/O: a
política recebe o hash do conteúdo e o canônico registrado e devolve a ação. O
registro em si é acessado por uma porta, implementada na infraestrutura, e a
coordenação é feita por :class:`DeduplicacaoConteudo`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

#: Piso mínimo de tamanho (bytes) para registrar o hash de um conteúdo.
TAMANHO_MINIMO_CONTEUDO = 1024


class HashRegistry(Protocol):
    """Contrato do registro de hashes de um escopo (ticker ou notícias)."""

    def canonico(self: "HashRegistry", digest: str) -> str | None:
        """Retorna o caminho relativo canônico do hash, ou ``None``."""
        ...

    def registrados(self: "HashRegistry") -> dict[str, str]:
        """Retorna o mapa ``hash -> caminho relativo`` registrado."""
        ...

    def registrar(self: "HashRegistry", digest: str, relativo: str) -> None:
        """Registra o hash apontando para o caminho relativo informado."""
        ...

    def remover(self: "HashRegistry", digest: str) -> None:
        """Remove a entrada do hash informado."""
        ...

    def remover_relativo(self: "HashRegistry", relativo: str) -> None:
        """Remove qualquer entrada cujo canônico seja o caminho relativo."""
        ...


def conteudo_hashavel(
    conteudo: bytes, *, minimo: int = TAMANHO_MINIMO_CONTEUDO
) -> bool:
    """Indica se o conteúdo tem tamanho mínimo para entrar no registro.

    Conteúdos vazios, só espaços ou abaixo do piso não são hasheados, para
    evitar que páginas genéricas curtas causem descarte indevido.
    """
    return len(conteudo) >= minimo and conteudo.strip() != b""


def eh_duplicata(
    digest: str,
    canonico: str | None,
    canonico_existe: bool,
    relativo: str,
) -> bool:
    """Indica se o conteúdo duplica um canônico existente e distinto.

    Sem canônico registrado, ou com canônico inexistente, o conteúdo é novo e
    pode ser registrado (a entrada inválida é substituída pelo novo caminho).
    """
    if canonico is None or not canonico_existe:
        return False
    return canonico != relativo


@dataclass(frozen=True)
class AvaliacaoDeduplicacao:
    """Resultado da avaliação de um conteúdo contra o registro."""

    digest: str | None
    duplicata: bool


class DeduplicacaoConteudo:
    """Coordena o registro de hashes e a decisão de persistir um conteúdo."""

    def __init__(
        self: "DeduplicacaoConteudo",
        registry: HashRegistry,
        hash_fn: Callable[[bytes], str],
        root: Path,
    ) -> None:
        """Inicializa o serviço com o registro, a função de hash e a raiz."""
        self._registry = registry
        self._hash = hash_fn
        self._root = Path(root)

    @property
    def root(self: "DeduplicacaoConteudo") -> Path:
        """Retorna a raiz de cache usada para derivar os caminhos relativos."""
        return self._root

    def relativo(self: "DeduplicacaoConteudo", caminho: Path) -> str:
        """Deriva o caminho relativo à raiz, tolerando caminhos externos."""
        try:
            return Path(caminho).relative_to(self._root).as_posix()
        except ValueError:
            return Path(caminho).name

    def avaliar(
        self: "DeduplicacaoConteudo", conteudo: bytes, caminho: Path
    ) -> AvaliacaoDeduplicacao:
        """Avalia se o conteúdo é duplicata do canônico já registrado."""
        if not conteudo_hashavel(conteudo):
            return AvaliacaoDeduplicacao(None, False)
        digest = self._hash(conteudo)
        relativo = self.relativo(caminho)
        canonico = self._registry.canonico(digest)
        canonico_existe = canonico is not None and (
            (self._root / canonico).is_file()
        )
        duplicata = eh_duplicata(digest, canonico, canonico_existe, relativo)
        return AvaliacaoDeduplicacao(digest, duplicata)

    def registrar(
        self: "DeduplicacaoConteudo", digest: str | None, caminho: Path
    ) -> None:
        """Registra o hash do conteúdo apontando para o caminho relativo."""
        if digest:
            self._registry.registrar(digest, self.relativo(caminho))

    def processar(
        self: "DeduplicacaoConteudo",
        conteudo: bytes,
        caminho: Path,
        gravar: Callable[[bytes], None],
    ) -> bool:
        """Grava o conteúdo e registra o hash quando não for duplicata.

        Retorna ``True`` quando o conteúdo foi gravado e ``False`` quando foi
        descartado por duplicidade.
        """
        avaliacao = self.avaliar(conteudo, caminho)
        if avaliacao.duplicata:
            return False
        gravar(conteudo)
        self.registrar(avaliacao.digest, caminho)
        return True
