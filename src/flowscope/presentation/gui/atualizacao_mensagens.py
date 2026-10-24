"""Mensagens do desfecho da aquisição de documentos e títulos."""

from __future__ import annotations

from flowscope.application.documentos.aquisicao import ResultadoAquisicao
from flowscope.presentation.gui.documentos_job import ResultadoAtualizacao


def mensagem_atualizacao(resultado: ResultadoAtualizacao) -> tuple[str, str]:
    """Monta a mensagem do desfecho combinado, distinguindo as etapas."""
    falhas = []
    if resultado.documentos.falhas:
        falhas.append(f"{resultado.documentos.falhas} documento(s)")
    if resultado.titulos.falhas:
        falhas.append(f"{resultado.titulos.falhas} fonte(s) de títulos")
    if falhas:
        return ("Falha em " + " e ".join(falhas) + ".", "⚠")
    partes = []
    if resultado.documentos.novos:
        partes.append("documentos")
    if resultado.titulos.novos or resultado.titulos.atualizados:
        partes.append("títulos")
    if partes:
        return (" e ".join(partes).capitalize() + " atualizados!", "")
    if resultado.titulos.sem_cnpj:
        return ("Nenhuma novidade; títulos sem CNPJ resolvido.", "ℹ")
    return ("Nenhuma novidade em documentos ou títulos.", "ℹ")


def mensagem_documentos(resultado: ResultadoAquisicao) -> tuple[str, str]:
    """Monta a mensagem do desfecho exclusivo de documentos."""
    if resultado.falhas:
        return (f"{resultado.falhas} documento(s) não baixado(s).", "⚠")
    if resultado.adquiridos:
        return ("Documentos atualizados!", "")
    return ("Nenhum documento novo.", "ℹ")
