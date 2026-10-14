"""Núcleo compartilhado de navegação da árvore de conhecimento."""

from flowscope.application.navegacao.core import (
    CAMPOS_OBRIGATORIOS,
    LIMITE_BUSCA,
    LIMITE_PAGINA_PADRAO,
    LIMITE_SEMANTICO,
    LIMITE_TRECHO,
    OPERACOES,
    TAMANHO_PAGINA_LISTAR,
    TIMEOUT_REGEX_MS,
    NavegacaoCore,
    Resultado,
)
from flowscope.application.navegacao.cursor import codificar, decodificar

__all__ = [
    "CAMPOS_OBRIGATORIOS",
    "LIMITE_BUSCA",
    "LIMITE_PAGINA_PADRAO",
    "LIMITE_SEMANTICO",
    "LIMITE_TRECHO",
    "OPERACOES",
    "TAMANHO_PAGINA_LISTAR",
    "TIMEOUT_REGEX_MS",
    "NavegacaoCore",
    "Resultado",
    "codificar",
    "decodificar",
]
