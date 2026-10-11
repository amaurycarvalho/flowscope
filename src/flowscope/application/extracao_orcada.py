"""Extração de texto com orçamento de tempo por documento.

A extração de PDF é executada em um processo separado para que uma página
patologicamente lenta não bloqueie a operação: o ``pypdf`` é Python puro e uma
chamada travada não pode ser interrompida dentro de uma thread (continua
consumindo o GIL). O processo filho extrai página a página e devolve o texto já
produzido ao pai; ao estourar o orçamento, o filho é encerrado e o resultado é o
texto parcial (``PARCIAL``, ou ``FALHA`` quando nenhuma página produziu texto).

A extração de HTML permanece no processo corrente, sem orçamento de tempo.
"""

from __future__ import annotations

import logging
import multiprocessing
import time
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Protocol

from flowscope.application.document_preview import (
    ExtracaoTexto,
    StatusExtracao,
    abrir_pdf,
    extrair_arquivo,
    iterar_paginas,
    montar_resultado,
)
from flowscope.log_paths import LOG_DATEFMT, LOG_FORMAT, log_file_path

logger = logging.getLogger("flowscope")

__all__ = ["EXTRACAO_TIMEOUT_S", "extrair_arquivo_com_orcamento"]

#: Orçamento de tempo (segundos) de extração por documento. DEVE ficar abaixo do
#: limite de inatividade do job de background (``LIMITE_INATIVIDADE_S``), pois a
#: extração bloqueia o worker sem publicar progresso; do contrário o watchdog
#: encerra o lote por inatividade.
EXTRACAO_TIMEOUT_S = 90.0

#: Tempo de carência (segundos) para colher o processo filho após a resposta.
EXTRACAO_GRACA_S = 5.0

#: Marcadores de mensagem trocadas entre o filho e o pai.
_PAGINA = "pagina"
_FIM = "fim"
_RESULTADO = "resultado"


@dataclass(frozen=True)
class _Acumulado:
    """Resultado parcial da leitura das mensagens do processo filho."""

    textos: tuple[str, ...]
    falhas: int
    concluiu: bool
    resultado: ExtracaoTexto | None = None


class _FonteMensagens(Protocol):
    """Fonte de mensagens com prazo, injetável para teste."""

    def ler(self: _FonteMensagens, timeout: float) -> tuple | None:
        """Devolve a próxima mensagem ou ``None`` quando o tempo esgota."""
        ...


class _FontePipe:
    """Fonte de mensagens ancorada na ponta de recebimento do ``Pipe``."""

    def __init__(self: _FontePipe, conexao: Connection) -> None:
        self._conexao = conexao

    def ler(self: _FontePipe, timeout: float) -> tuple | None:
        """Recebe a próxima mensagem, aguardando até ``timeout`` segundos."""
        if timeout <= 0:
            return None
        if self._conexao.poll(timeout):
            return self._conexao.recv()
        return None


def extrair_arquivo_com_orcamento(
    caminho: Path,
    seletor: str | None = None,
    senha: str | None = None,
    *,
    timeout: float = EXTRACAO_TIMEOUT_S,
) -> ExtracaoTexto:
    """Extrai o texto de ``caminho`` limitando a extração de PDF a ``timeout``.

    HTML é extraído no processo corrente. PDF é extraído em um processo
    separado; ao estourar o orçamento, o processo é encerrado e o resultado é o
    texto parcial já produzido (``PARCIAL``, ou ``FALHA`` sem texto). Nunca
    propaga exceção da biblioteca de extração.
    """
    if Path(caminho).suffix.lower() != ".pdf":
        return extrair_arquivo(caminho, seletor, senha)
    return _extrair_pdf_orcado(Path(caminho), senha, timeout)


def _extrair_pdf_orcado(
    caminho: Path, senha: str | None, timeout: float
) -> ExtracaoTexto:
    """Executa a extração do PDF em processo separado com prazo rígido."""
    contexto = multiprocessing.get_context("spawn")
    receber, enviar = contexto.Pipe(duplex=False)
    processo = contexto.Process(
        target=_extrair_pdf_filho,
        args=(str(caminho), senha, enviar),
        daemon=True,
    )
    processo.start()
    enviar.close()
    try:
        acumulado = _consumir(_FontePipe(receber), timeout, time.monotonic)
    finally:
        receber.close()
    _finalizar(processo, forcar=not acumulado.concluiu)
    return _resultado_de(acumulado)


def _resultado_de(acumulado: _Acumulado) -> ExtracaoTexto:
    """Deriva o resultado do acumulado, forçando parcial no estouro.

    Um resultado interrompido nunca é ``SEM_TEXTO``: soma-se a página
    interrompida às falhas, de modo que haja texto → ``PARCIAL`` e sem texto →
    ``FALHA``.
    """
    if acumulado.resultado is not None:
        return acumulado.resultado
    if acumulado.concluiu:
        return montar_resultado(list(acumulado.textos), acumulado.falhas)
    return montar_resultado(list(acumulado.textos), acumulado.falhas + 1)


def _consumir(
    fonte: _FonteMensagens,
    timeout: float,
    relogio: Callable[[], float],
) -> _Acumulado:
    """Acumula as mensagens do filho até o fim ou o estouro do prazo.

    Função pura quanto a I/O: recebe uma fonte de mensagens e um relógio
    injetáveis, o que a torna testável de forma determinística.
    """
    textos: list[str] = []
    falhas = 0
    fim = relogio() + timeout
    while True:
        restante = fim - relogio()
        if restante <= 0:
            return _Acumulado(tuple(textos), falhas, False)
        mensagem = fonte.ler(restante)
        if mensagem is None:
            return _Acumulado(tuple(textos), falhas, False)
        tipo = mensagem[0]
        if tipo == _FIM:
            return _Acumulado(tuple(textos), falhas, True)
        if tipo == _RESULTADO:
            _, texto, status, paginas = mensagem
            return _Acumulado(
                tuple(textos),
                falhas,
                True,
                ExtracaoTexto(texto, StatusExtracao(status), paginas),
            )
        _, texto, falhou = mensagem
        if falhou:
            falhas += 1
        else:
            textos.append(texto)


def _finalizar(processo: BaseProcess, *, forcar: bool) -> None:
    """Colhe o processo filho, encerrando-o antes quando o prazo estourou."""
    if forcar and processo.is_alive():
        processo.terminate()
    processo.join(EXTRACAO_GRACA_S)
    if processo.is_alive():
        processo.kill()
        processo.join(EXTRACAO_GRACA_S)


def _configurar_log_pypdf(caminho: Path | None = None) -> None:
    """Silencia o ``pypdf`` abaixo de ``ERROR`` e grava ``ERROR``+ no log do app.

    O worker separado não herda a configuração de logging do processo principal,
    então configura o logger ``pypdf`` por conta própria: os avisos de
    autorreparo de PDFs malformados deixam de vazar para o ``stderr`` e os erros
    reais ficam auditáveis no arquivo de log. Idempotente: não adiciona um
    segundo handler de arquivo.
    """
    logger_pypdf = logging.getLogger("pypdf")
    logger_pypdf.setLevel(logging.ERROR)
    if any(
        isinstance(handler, logging.FileHandler)
        for handler in logger_pypdf.handlers
    ):
        logger_pypdf.propagate = False
        return
    destino = caminho if caminho is not None else log_file_path()
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = logging.FileHandler(destino, encoding="utf-8")
    except OSError:  # sem log gravável, evita ao menos o vazamento no console
        logger_pypdf.propagate = False
        return
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT))
    logger_pypdf.addHandler(handler)
    logger_pypdf.propagate = False


def _extrair_pdf_filho(caminho: str, senha: str | None, conexao: Connection) -> None:
    """Alvo do processo filho: extrai páginas e as transmite ao pai."""
    _configurar_log_pypdf()
    try:
        dados = Path(caminho).read_bytes()
    except OSError:
        conexao.send((_RESULTADO, "", StatusExtracao.FALHA.value, 0))
        return
    leitor, erro = abrir_pdf(dados, senha)
    if erro is not None:
        conexao.send(
            (_RESULTADO, erro.texto, erro.status.value, erro.paginas_com_falha)
        )
        return
    gerador = iterar_paginas(leitor)
    if gerador is None:
        conexao.send((_RESULTADO, "", StatusExtracao.FALHA.value, 0))
        return
    try:
        for texto, falhou in gerador:
            conexao.send((_PAGINA, texto, falhou))
        conexao.send((_FIM,))
    except Exception:  # falha inesperada ao transmitir as páginas
        logger.warning("Falha ao transmitir páginas do PDF", exc_info=True)
        conexao.send((_RESULTADO, "", StatusExtracao.FALHA.value, 0))
