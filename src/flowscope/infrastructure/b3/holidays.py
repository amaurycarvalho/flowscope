"""Feriados nacionais observados no calendário de negociação da B3.

Reexporta a definição do domínio para preservar o caminho de importação
histórico sem duplicar a lista.
"""

from flowscope.domain.b3.calendario import FERIADOS_NACIONAIS

__all__ = ["FERIADOS_NACIONAIS"]
