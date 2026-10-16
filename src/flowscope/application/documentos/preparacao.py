"""Preparação de texto dos documentos, na camada de aplicação.

Extrai o texto com orçamento e persiste apenas resultados definitivos (texto
completo ou ausência conclusiva de texto). Resultados parciais, de falha ou
protegidos permanecem pendentes para nova tentativa. Não toca em widgets nem
em serviços de apresentação: recebe as portas de extração, de persistência e de
leitura de cache por injeção, de modo a ser reusada pela GUI e pela CLI.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
    tem_texto,
)
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.documents.texto import SEM_TEXTO

logger = logging.getLogger("flowscope")


class PreparacaoTexto:
    """Prepara o texto de um documento, persistindo só resultados definitivos."""

    def __init__(
        self: PreparacaoTexto,
        ler_cache: Callable[[DocumentoArquivo], str | None],
        extrair: Callable[[DocumentoArquivo, str | None], ExtracaoTexto],
        chave: Callable[[DocumentoArquivo], str],
        salvar: Callable[[str, str, str], None],
        memo: dict | None = None,
    ) -> None:
        """Guarda as portas de leitura de cache, extração, chave e persistência."""
        self._ler_cache = ler_cache
        self._extrair = extrair
        self._chave = chave
        self._salvar = salvar
        self._memo = memo

    def preparar(
        self: PreparacaoTexto, arquivo: DocumentoArquivo, senha: str | None = None
    ) -> ExtracaoTexto:
        """Retorna o texto do documento, gravando e memoizando só em *miss*."""
        texto = self._ler_cache(arquivo)
        if texto is not None:
            status = (
                StatusExtracao.OK if tem_texto(texto) else StatusExtracao.SEM_TEXTO
            )
            return ExtracaoTexto(texto, status)
        resultado = self._extrair(arquivo, senha)
        self._registrar(resultado, arquivo)
        if resultado.status in (StatusExtracao.OK, StatusExtracao.SEM_TEXTO):
            self._salvar(
                arquivo.ticker, self._chave(arquivo), resultado.texto or SEM_TEXTO
            )
            if self._memo is not None:
                self._memo[arquivo.caminho] = resultado.texto
        return resultado

    @staticmethod
    def _registrar(resultado: ExtracaoTexto, arquivo: DocumentoArquivo) -> None:
        """Registra o motivo de uma extração não conclusiva, para diagnóstico."""
        if resultado.status is StatusExtracao.PARCIAL:
            logger.warning(
                "Extração parcial (%d página(s) com falha): %s/%s",
                resultado.paginas_com_falha,
                arquivo.ticker,
                arquivo.nome,
            )
        elif resultado.status is StatusExtracao.FALHA:
            logger.warning(
                "Falha crítica de extração: %s/%s", arquivo.ticker, arquivo.nome
            )
        elif resultado.status is StatusExtracao.SEM_TEXTO:
            logger.warning(
                "Documento sem texto extraível: %s/%s", arquivo.ticker, arquivo.nome
            )
