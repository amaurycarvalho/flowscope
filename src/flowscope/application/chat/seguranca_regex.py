"""Segurança da busca por expressão regular do chat.

Compila padrões fornecidos pela LLM com proteção contra ReDoS: timeout por
busca (biblioteca ``regex``, quando disponível), bloqueio heurístico de padrões
catastróficos e, como fallback sem a biblioteca, o ``re`` da stdlib com teto de
tamanho de padrão.
"""

from __future__ import annotations

import re

try:  # dependência opcional do grupo [llm]
    import regex as _regex  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - ambiente sem a dependência opcional
    _regex = None

#: Timeout padrão de uma busca, em milissegundos.
TIMEOUT_PADRAO_MS = 100

#: Teto de tamanho de padrão aceito no fallback sem a biblioteca ``regex``.
LIMITE_PADRAO_FALLBACK = 1000

#: Padrões considerados catastróficos: backreferences e quantificadores aninhados.
_BACKREFERENCE = re.compile(r"\\[1-9]")
_ANINHADO = re.compile(r"\([^()]*[+*][^()]*\)[+*]")
_REPETICAO_SOLTA = re.compile(r"\.\*\.\*")


class PadraoInvalido(Exception):
    """Padrão sintaticamente inválido."""


class PadraoBloqueado(Exception):
    """Padrão recusado pela heurística de segurança."""


class TimeoutRegex(Exception):
    """Busca abortada por exceder o timeout."""


def _catastrofico(padrao: str) -> bool:
    """Heurística conservadora de padrões potencialmente catastróficos."""
    return bool(
        _BACKREFERENCE.search(padrao)
        or _ANINHADO.search(padrao)
        or _REPETICAO_SOLTA.search(padrao)
    )


class BuscaRegex:
    """Padrão compilado com timeout e proteção contra ReDoS."""

    def __init__(
        self: BuscaRegex,
        padrao: str,
        timeout_ms: int = TIMEOUT_PADRAO_MS,
    ) -> None:
        """Compila o padrão, recusando os bloqueados ou inválidos."""
        if _catastrofico(padrao):
            raise PadraoBloqueado("padrao_catastrofico")
        self._timeout_s = timeout_ms / 1000.0
        self._com_timeout = _regex is not None
        self._compilado = self._compilar(padrao)

    @staticmethod
    def _compilar(padrao: str) -> object:
        """Compila com ``regex`` quando disponível; senão, com ``re``."""
        if _regex is not None:
            try:
                return _regex.compile(padrao)
            except _regex.error as exc:  # type: ignore[union-attr]
                raise PadraoInvalido(str(exc)) from exc
        if len(padrao) > LIMITE_PADRAO_FALLBACK:
            raise PadraoBloqueado("padrao_grande")
        try:
            return re.compile(padrao)
        except re.error as exc:
            raise PadraoInvalido(str(exc)) from exc

    def buscar(self: BuscaRegex, texto: str) -> bool:
        """Indica se o texto casa, abortando com ``TimeoutRegex`` se exceder."""
        if not self._com_timeout:
            return bool(self._compilado.search(texto))  # type: ignore[attr-defined]
        try:
            return bool(
                self._compilado.search(texto, timeout=self._timeout_s)  # type: ignore[attr-defined]
            )
        except TimeoutError as exc:
            raise TimeoutRegex(str(exc)) from exc


def compilar(padrao: str, timeout_ms: int = TIMEOUT_PADRAO_MS) -> BuscaRegex:
    """Compila um padrão seguro para a operação ``buscar`` do protocolo."""
    return BuscaRegex(padrao, timeout_ms=timeout_ms)
