"""Testes do modelo, das chaves e da árvore de títulos de renda fixa."""

from datetime import date
from decimal import Decimal

import pytest

from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    CarteiraTitulos,
    PapelTitulo,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
    chave_fii,
    chave_fonte,
    chave_fre,
    chave_securit,
    cnpj_valido,
    id_curto,
    montar_arvore,
)


class TestModelo:
    def test_rotulos_de_exibicao(self):
        assert TipoTitulo.DEBENTURE.rotulo == "Debêntures"
        assert TipoTitulo.LETRA_FINANCEIRA.rotulo == "Letras Financeiras"
        assert TipoTitulo.CRI.segmento == "cri"
        assert PapelTitulo.OBRIGACAO.segmento == "obrigacoes"
        assert PapelTitulo.DIREITO.rotulo == "Direitos"

    def test_titulo_usa_identificacao_como_rotulo(self):
        titulo = TituloRendaFixa(
            tipo=TipoTitulo.DEBENTURE,
            papel=PapelTitulo.OBRIGACAO,
            identificacao="PETR27",
        )
        assert titulo.nome_exibicao == "PETR27"

    def test_agregado_e_ausencia_tem_rotulos_distintos(self):
        agregado = TituloAgregado(TipoTitulo.CDB, PapelTitulo.DIREITO)
        ausencia = AusenciaFonte(TipoTitulo.CDB, PapelTitulo.OBRIGACAO)
        assert "agregado" in agregado.rotulo
        assert "sem fonte" in ausencia.rotulo


class TestChaves:
    def test_chave_e_id_estaveis(self):
        chave = chave_fre(
            "33000167000101",
            "debenture",
            "PETR27",
            date(2020, 1, 1),
            date(2030, 1, 1),
            Decimal(1000),
            Decimal("1000.50"),
        )
        assert chave == chave_fre(
            "33000167000101",
            "debenture",
            "PETR27",
            date(2020, 1, 1),
            date(2030, 1, 1),
            Decimal(1000),
            Decimal("1000.50"),
        )
        assert id_curto(chave) == id_curto(chave)
        assert len(id_curto(chave)) == 10

    def test_chaves_por_fonte(self):
        assert chave_securit("18K0669354", None, None, None) == "18K0669354"
        assert chave_fii("18K0669354", None, None, None, None) == "18K0669354"
        assert chave_securit(None, "BRCRI123", None, None) == "BRCRI123"
        assert "|" in chave_securit(None, None, "123", "456")

    def test_rejeita_caractere_invalido(self):
        with pytest.raises(ValueError):
            chave_fonte(("a|b",))
        with pytest.raises(ValueError):
            chave_fonte(("a\nb",))

    def test_cnpj_valido(self):
        assert cnpj_valido("33.000.167/0001-01")
        assert not cnpj_valido("00000000000000")
        assert not cnpj_valido("123")
        assert not cnpj_valido("33000167000102")


class TestArvore:
    def test_companhia_com_debenture_e_sem_fonte(self):
        carteira = CarteiraTitulos(
            ticker="PETR4",
            tipo_ativo="acao",
            obrigacoes=(
                TituloRendaFixa(
                    tipo=TipoTitulo.DEBENTURE,
                    papel=PapelTitulo.OBRIGACAO,
                    id="d1",
                    identificacao="PETR27",
                ),
            ),
        )
        arvore = montar_arvore(carteira)
        tipos = {galho.tipo: galho for galho in arvore.obrigacoes.tipos}
        assert tipos[TipoTitulo.DEBENTURE].itens[0].id == "d1"
        assert isinstance(tipos[TipoTitulo.CDB].itens[0], AusenciaFonte)
        assert not arvore.direitos.tipos

    def test_fii_com_cri_e_agregado(self):
        carteira = CarteiraTitulos(
            ticker="ALZR11",
            tipo_ativo="fii",
            direitos=(
                TituloRendaFixa(
                    tipo=TipoTitulo.CRI,
                    papel=PapelTitulo.DIREITO,
                    id="c1",
                ),
            ),
            agregados=(
                TituloAgregado(
                    TipoTitulo.DEBENTURE,
                    PapelTitulo.DIREITO,
                    valor=Decimal(10),
                ),
            ),
        )
        arvore = montar_arvore(carteira)
        tipos = {galho.tipo: galho for galho in arvore.direitos.tipos}
        assert isinstance(tipos[TipoTitulo.CRI].itens[0], TituloRendaFixa)
        assert isinstance(tipos[TipoTitulo.DEBENTURE].itens[0], TituloAgregado)
        assert not arvore.obrigacoes.tipos

    def test_ramo_vazio(self):
        arvore = montar_arvore(None)
        assert arvore.vazio
