"""Verificação da última versão publicada do FlowScope.

A consulta à release publicada é uma porta de aplicação: a apresentação
fornece um ``ReleaseChecker`` (o adaptador HTTP vive em ``infrastructure``) e a
decisão de haver versão mais nova usa a regra de domínio ``is_newer``.
"""

from collections.abc import Callable

from flowscope.domain.version import is_newer

#: Consulta a última release publicada, devolvendo ``(versao, url)`` ou ``None``.
ReleaseChecker = Callable[[], tuple[str, str] | None]


def verificar_nova_versao(
    versao_atual: str, checker: ReleaseChecker,
) -> tuple[str, str] | None:
    """Retorna ``(versao, url)`` quando a release publicada é mais nova.

    Retorna ``None`` quando a consulta não devolve resultado ou quando a
    versão publicada não é mais nova que ``versao_atual``.
    """
    resultado = checker()
    if resultado is None:
        return None
    versao, url = resultado
    if not is_newer(versao, versao_atual):
        return None
    return versao, url
