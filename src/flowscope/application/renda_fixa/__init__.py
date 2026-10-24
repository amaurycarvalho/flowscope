"""Casos de uso, portas e renderização dos títulos de renda fixa."""

from flowscope.application.renda_fixa.aquisicao import AquisicaoTitulos
from flowscope.application.renda_fixa.assinatura import assinatura_conteudo
from flowscope.application.renda_fixa.consulta import ConsultarTitulosUseCase
from flowscope.application.renda_fixa.inferencia import (
    CATEGORIAS_ELEGIVEIS,
    InferirDireitosObrigacoesUseCase,
)
from flowscope.application.renda_fixa.portas import (
    FonteTitulos,
    InferenciasRepository,
    TitulosRepository,
)
from flowscope.application.renda_fixa.render import (
    render_adicionais,
    render_agregado,
    render_ausencia,
    render_data_referencia,
    render_documentos,
    render_geral,
    render_inferencia,
    render_inferencia_documento,
    render_inferencia_geral,
    render_inferencia_proveniencia,
    render_ltv_titulo,
    render_titulo,
)
from flowscope.application.renda_fixa.resultados import (
    ResultadoAquisicaoTitulos,
    ResultadoFontes,
    ResultadoInferencia,
)
from flowscope.application.renda_fixa.serializacao import (
    carteira_de_dict,
    carteira_para_dict,
)
from flowscope.application.renda_fixa.serializacao_inferencias import (
    carteira_inferencias_de_dict,
    carteira_inferencias_para_dict,
)

__all__ = [
    "CATEGORIAS_ELEGIVEIS",
    "AquisicaoTitulos",
    "ConsultarTitulosUseCase",
    "FonteTitulos",
    "InferenciasRepository",
    "InferirDireitosObrigacoesUseCase",
    "ResultadoAquisicaoTitulos",
    "ResultadoFontes",
    "ResultadoInferencia",
    "TitulosRepository",
    "assinatura_conteudo",
    "carteira_de_dict",
    "carteira_inferencias_de_dict",
    "carteira_inferencias_para_dict",
    "carteira_para_dict",
    "render_adicionais",
    "render_agregado",
    "render_ausencia",
    "render_data_referencia",
    "render_documentos",
    "render_geral",
    "render_inferencia",
    "render_inferencia_documento",
    "render_inferencia_geral",
    "render_inferencia_proveniencia",
    "render_ltv_titulo",
    "render_titulo",
]
