"""Regras e varredura das fronteiras de dependência entre camadas.

Centraliza a tabela de imports proibidos, a varredura AST dos módulos de
``src/flowscope`` e a comparação com a allowlist de violações legadas. É
consumido pelo teste de fronteira (:mod:`test_layer_boundaries`) e pelos
testes sintéticos da lógica de comparação.
"""

from __future__ import annotations

import ast
from pathlib import Path

#: Camadas arquiteturais do FlowScope, da mais interna para a mais externa.
LAYERS: tuple[str, ...] = (
    "domain",
    "application",
    "infrastructure",
    "presentation",
)

#: Camadas que cada camada NÃO pode importar, no fluxo unidirecional
#: ``presentation -> application -> domain`` e ``infrastructure -> application``.
FORBIDDEN_IMPORTS: dict[str, frozenset[str]] = {
    "domain": frozenset({"application", "infrastructure", "presentation"}),
    "application": frozenset({"infrastructure", "presentation"}),
    "infrastructure": frozenset({"presentation"}),
    "presentation": frozenset({"infrastructure"}),
}

#: Pontos de composição: única exceção estrutural a ``presentation -> infrastructure``.
COMPOSITION_ROOT: frozenset[str] = frozenset(
    {
        "presentation/cli.py",
        "presentation/main.py",
        "presentation/gui/app_wiring.py",
    }
)

#: Par ``(caminho relativo a src/flowscope, camada importada)`` de uma violação.
Violation = tuple[str, str]

_LAYER_PREFIX = "flowscope."


def imported_layers(source: str) -> set[str]:
    """Retorna as camadas do FlowScope importadas por um trecho de código."""
    arvore = ast.parse(source)
    camadas: set[str] = set()
    for no in ast.walk(arvore):
        modulos: list[str] = []
        if isinstance(no, ast.Import):
            modulos = [alias.name for alias in no.names]
        elif isinstance(no, ast.ImportFrom) and no.module:
            modulos = [no.module]
        for modulo in modulos:
            if not modulo.startswith(_LAYER_PREFIX):
                continue
            partes = modulo.split(".")
            if len(partes) >= 2 and partes[1] in LAYERS:
                camadas.add(partes[1])
    return camadas


def is_exempt(caminho: str, origem: str, destino: str) -> bool:
    """Indica se a violação está dispensada estruturalmente (composition root)."""
    return (
        origem == "presentation"
        and destino == "infrastructure"
        and caminho in COMPOSITION_ROOT
    )


def find_violations(src_dir: Path) -> set[Violation]:
    """Varre ``src_dir`` e retorna as violações de fronteira encontradas.

    As violações dos pontos de composição (``COMPOSITION_ROOT``) não são
    reportadas: são a exceção estrutural permitida para ``presentation``.
    """
    violacoes: set[Violation] = set()
    for caminho in sorted(src_dir.rglob("*.py")):
        relativo = caminho.relative_to(src_dir)
        origem = relativo.parts[0]
        if origem not in LAYERS:
            continue
        proibidas = FORBIDDEN_IMPORTS[origem]
        for destino in imported_layers(caminho.read_text(encoding="utf-8")):
            if destino not in proibidas:
                continue
            chave = relativo.as_posix()
            if is_exempt(chave, origem, destino):
                continue
            violacoes.add((chave, destino))
    return violacoes


def read_allowlist(path: Path) -> set[Violation]:
    """Lê a allowlist de violações legadas (``caminho -> camada`` por linha)."""
    entradas: set[Violation] = set()
    for linha in path.read_text(encoding="utf-8").splitlines():
        conteudo = linha.split("#", 1)[0].strip()
        if not conteudo:
            continue
        caminho, _, destino = conteudo.partition("->")
        entradas.add((caminho.strip(), destino.strip()))
    return entradas


def unlisted_violations(
    violations: set[Violation], allowed: set[Violation]
) -> set[Violation]:
    """Violações encontradas que não constam na allowlist (reprovam)."""
    return set(violations) - set(allowed)


def stale_allowlist_entries(
    violations: set[Violation], allowed: set[Violation]
) -> set[Violation]:
    """Entradas da allowlist sem violação correspondente (reprovam)."""
    return set(allowed) - set(violations)
