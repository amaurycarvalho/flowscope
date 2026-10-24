"""Trabalho em background do resumo em lote dos documentos pendentes.

A orquestração pura vive na camada de aplicação
(:mod:`flowscope.application.documentos.lote_execucao`); este módulo apenas
fixa o grupo de exclusão e a política do trabalho e reexporta os nomes usados
pela apresentação. O contexto do job (``JobContext``) satisfaz a interface
mínima de progresso/cancelamento da orquestração.
"""

from flowscope.application.documentos.lote_execucao import (
    FASE_INFERIR,
    FASE_PREPARAR,
    FASE_RESUMIR,
    InferenciaLote,
    MotivoExtracao,
    PainelDocumentos,
    ResultadoResumos,
    _motivo,
    _preparar_textos,
    _resumir,
    executar_resumos,
)
from flowscope.application.finalizacao_extracao import ItemPendente
from flowscope.presentation.gui.background.job import Politica

__all__ = [
    "FASE_INFERIR",
    "FASE_PREPARAR",
    "FASE_RESUMIR",
    "GRUPO",
    "POLITICA",
    "InferenciaLote",
    "ItemPendente",
    "MotivoExtracao",
    "PainelDocumentos",
    "ResultadoResumos",
    "_motivo",
    "_preparar_textos",
    "_resumir",
    "executar_resumos",
]

#: Grupo de exclusão e política do resumo em lote.
GRUPO = "resumos"
POLITICA = Politica.LATEST_WINS
