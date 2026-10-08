"""Eventos tipados publicados pelos jobs assíncronos.

Os eventos são valores imutáveis produzidos na thread de trabalho e entregues
aos callbacks na thread do Tk pelo pump do gerenciador. Eles são o único canal
de comunicação entre o worker e a interface.
"""

import threading
from dataclasses import dataclass, field
from enum import Enum


class Outcome(Enum):
    """Desfecho terminal de um job, declarado pelo worker ou por escape."""

    SUCESSO = "sucesso"
    FALHA = "falha"
    CANCELADO = "cancelado"
    ABORTADO = "abortado"


@dataclass(frozen=True)
class Progresso:
    """Progresso de uma unidade de trabalho."""

    detalhe: str = ""
    atual: int | None = None
    total: int | None = None
    dados: object = None


@dataclass(frozen=True)
class Resultado:
    """Resultado final ou por item de um trabalho."""

    valor: object = None
    falhou: bool = False
    dados: object = None


@dataclass(frozen=True)
class Erro:
    """Falha ocorrida durante o trabalho, possivelmente por item.

    ``fatal`` distingue a falha declarada do job (``True``, encerra em
    ``FALHA``) da falha de um item recuperada pelo trabalho (``False``).
    """

    excecao: BaseException
    dados: object = None
    fatal: bool = False


@dataclass(frozen=True)
class Termino:
    """Término do job, carregando o desfecho terminal.

    ``cancelado`` é propriedade derivada de ``outcome`` para compatibilidade.
    """

    outcome: Outcome = Outcome.SUCESSO
    falha_reportada: bool = False

    @property
    def cancelado(self: "Termino") -> bool:
        """Indica se o desfecho do job foi ``CANCELADO``."""
        return self.outcome is Outcome.CANCELADO


@dataclass(frozen=True)
class Confirmacao:
    """Pedido de confirmação do worker à interface, com resposta síncrona.

    O worker publica o evento e bloqueia em ``evento``; a interface atende o
    pedido na thread do Tk, grava a resposta em ``caixa`` e libera o worker.
    """

    quantidade: int
    nomes: list[str] = field(default_factory=list)
    evento: threading.Event = field(default_factory=threading.Event)
    caixa: dict = field(default_factory=dict)
    motivo: str = "documentos"


#: União dos eventos que um job pode publicar.
Evento = Progresso | Resultado | Erro | Termino | Confirmacao
