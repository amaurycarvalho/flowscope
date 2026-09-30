"""Montagem da árvore de conhecimento a partir das fontes locais.

Cada fonte é um provedor de ramo: constrói o seu ``No`` a partir do cache
local e o devolve. O montador agrega os ramos sob a raiz, tolerando falhas de
uma fonte sem derrubar as demais, e deriva a assinatura do estado.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Protocol

from flowscope.application.chat.arvore import ArvoreConhecimento, No, no_interno
from flowscope.application.chat.manifesto import assinatura_estado

logger = logging.getLogger("flowscope")


class FonteArvore(Protocol):
    """Provedor de um ramo da árvore a partir do cache local."""

    def construir(self: FonteArvore) -> No | None:
        """Constrói o ramo da fonte, ou ``None`` quando não há dado."""
        ...


class MontarArvore:
    """Agrega as fontes de ramos em uma ``ArvoreConhecimento``."""

    def __init__(
        self: MontarArvore,
        fontes: Iterable[FonteArvore],
        backend_semantico: object | None = None,
    ) -> None:
        """Guarda as fontes e o backend de busca semântica opcional."""
        self._fontes = list(fontes)
        self._backend = backend_semantico

    def montar(
        self: MontarArvore,
        caminhos: Iterable = (),
        watchlist: Iterable[str] = (),
    ) -> ArvoreConhecimento:
        """Monta a árvore agregando os ramos das fontes disponíveis."""
        raiz = no_interno("/", "/")
        for fonte in self._fontes:
            try:
                no = fonte.construir()
            except Exception:
                logger.warning(
                    "Fonte de ramo da árvore falhou; ignorando.", exc_info=True
                )
                continue
            if no is not None:
                raiz.filho(no)
        return ArvoreConhecimento(
            raiz,
            assinatura=assinatura_estado(caminhos, watchlist),
            backend_semantico=self._backend,
        )
