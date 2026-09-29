"""Eventos tipados publicados pelos jobs assíncronos.

Os eventos são valores imutáveis produzidos na thread de trabalho e entregues
aos callbacks na thread do Tk pelo pump do gerenciador. Eles são o único canal
de comunicação entre o worker e a interface.
"""

from dataclasses import dataclass


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
    """Falha ocorrida durante o trabalho, possivelmente por item."""

    excecao: BaseException
    dados: object = None


@dataclass(frozen=True)
class Termino:
    """Término do job, indicando se foi cancelado."""

    cancelado: bool = False


#: União dos eventos que um job pode publicar.
Evento = Progresso | Resultado | Erro | Termino
