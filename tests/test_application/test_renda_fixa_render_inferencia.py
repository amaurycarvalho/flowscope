"""Testes da renderização dos itens inferidos de renda fixa."""

from datetime import date

from flowscope.application.renda_fixa import (
    render_inferencia,
    render_inferencia_documento,
    render_inferencia_geral,
    render_inferencia_proveniencia,
)
from flowscope.domain.renda_fixa import (
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
)


def _item() -> InferenciaTitulo:
    return InferenciaTitulo(
        tipo=TipoTitulo.CRI,
        papel=PapelTitulo.DIREITO,
        descricao="CRI da emissora Alfa",
        documento="relatorio.pdf",
        chave_documento="documentos-relevantes/ALZR11/2026/02/10.pdf",
        trecho="O fundo mantém CRI da emissora Alfa.",
        confianca=0.82,
        data_referencia=date(2026, 2, 1),
    )


class TestRenderInferencia:
    def test_geral_declara_a_origem_por_ia(self):
        texto = render_inferencia_geral(_item())
        assert "CRI" in texto
        assert "inferido pela IA" in texto
        assert "82%" in texto

    def test_proveniencia_exibe_documento_data_e_trecho(self):
        texto = render_inferencia_proveniencia(_item())
        assert "relatorio.pdf" in texto
        assert "2026-02-01" in texto
        assert "O fundo mantém CRI" in texto

    def test_documento_exibe_a_chave_de_origem(self):
        texto = render_inferencia_documento(_item())
        assert "relatorio.pdf" in texto
        assert "documentos-relevantes/ALZR11/2026/02/10.pdf" in texto

    def test_render_completo_reune_geral_e_proveniencia(self):
        texto = render_inferencia(_item())
        assert "inferido pela IA" in texto
        assert "relatorio.pdf" in texto
