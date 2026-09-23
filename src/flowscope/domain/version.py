"""Comparação semântica de versões no formato ``X.Y.Z``."""

import re

_VERSAO_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$", re.IGNORECASE)


def parse_version(texto: str) -> tuple[int, int, int] | None:
    """Interpreta ``texto`` como uma versão de três segmentos numéricos.

    É tolerante ao prefixo ``v`` (por exemplo, ``v1.2.0``) e a entradas
    inválidas: em vez de lançar exceção, retorna ``None``.
    """
    if not isinstance(texto, str):
        return None
    encontrado = _VERSAO_RE.match(texto.strip())
    if encontrado is None:
        return None
    maior, menor, correcao = (int(parte) for parte in encontrado.groups())
    return (maior, menor, correcao)


def is_newer(publicada: str, atual: str) -> bool:
    """Indica se ``publicada`` é estritamente mais nova que ``atual``.

    Versões inválidas em qualquer um dos lados resultam em ``False``.
    """
    nova = parse_version(publicada)
    base = parse_version(atual)
    if nova is None or base is None:
        return False
    return nova > base
