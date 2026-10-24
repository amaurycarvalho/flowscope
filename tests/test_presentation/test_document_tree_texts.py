"""Testes headless dos textos de pré-visualização do ramo de direitos."""

from datetime import date

from flowscope.domain.renda_fixa import (
    CarteiraTitulos,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
    TituloRendaFixa,
    montar_arvore,
)
from flowscope.presentation.gui.charts.document_tree_view import (
    _texto_ramo,
    _texto_tipo,
    _texto_tipos,
)


def _carteira() -> CarteiraTitulos:
    return CarteiraTitulos(
        ticker="HGBS11",
        tipo_ativo="fii",
        direitos=(
            TituloRendaFixa(
                tipo=TipoTitulo.CRI,
                papel=PapelTitulo.DIREITO,
                id="c1",
                chave_fonte="c1",
                rotulo="GAIA SECURITIZADORA S.A. - 12E0031967",
                identificacao="12E0031967",
                cnpj_emissor="7587384000130",
                data_referencia=date(2026, 6, 30),
            ),
            TituloRendaFixa(
                tipo=TipoTitulo.LCI,
                papel=PapelTitulo.DIREITO,
                id="l1",
                chave_fonte="l1",
                rotulo="CAIXA ECONOMICA",
                cnpj_emissor="360305000104",
                data_referencia=date(2025, 9, 30),
            ),
        ),
    )


class TestTextosDoRamo:
    def test_ramo_resume_os_dois_papeis(self):
        arvore = montar_arvore(_carteira())
        texto = _texto_ramo(arvore)
        assert "Obrigações: 0 item(ns)" in texto
        assert "Direitos: 2 item(ns)" in texto

    def test_ramo_vazio_mantem_ausencia_explicita(self):
        assert "Sem dados de Direitos e Obrigações." in _texto_ramo(None)

    def test_titulos_resume_os_tipos(self):
        arvore = montar_arvore(_carteira())
        texto = _texto_tipos(PapelTitulo.DIREITO, arvore.direitos.tipos)
        assert "CRI: 1 item(ns)" in texto
        assert "LCI: 1 item(ns)" in texto

    def test_tipo_lista_itens_com_data(self):
        arvore = montar_arvore(_carteira())
        cri = arvore.direitos.tipos[0]
        texto = _texto_tipo(cri)
        assert "12E0031967" in texto
        assert "2026-06-30" in texto

    def test_tipo_lista_item_inferido(self):
        item = InferenciaTitulo(
            tipo=TipoTitulo.CRI,
            papel=PapelTitulo.DIREITO,
            descricao="CRI inferido",
            documento="relatorio.pdf",
            trecho="evidência",
            data_referencia=date(2026, 2, 1),
        )
        arvore = montar_arvore(None, [item])
        texto = _texto_tipo(arvore.direitos.tipos[0])
        assert "CRI inferido" in texto
