"""Testes headless das regras puras da finalização de extração."""

import pytest

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.finalizacao_extracao import (
    ItemPendente,
    nota_extracao,
    resumo_deterministico,
    texto_definitivo,
)
from flowscope.application.resumo_documento import resumo_completo


class TestNotaExtracao:
    def test_parcial_informa_quantidade_de_paginas(self):
        nota = nota_extracao(StatusExtracao.PARCIAL, 3)

        assert "parcial" in nota.lower()
        assert "3" in nota

    def test_falha_descreve_erro_critico(self):
        nota = nota_extracao(StatusExtracao.FALHA)

        assert "erro crítico" in nota.lower()

    def test_protegido_descreve_senha(self):
        nota = nota_extracao(StatusExtracao.PROTEGIDO)

        assert "senha" in nota.lower()

    def test_status_nao_finalizavel_levanta(self):
        with pytest.raises(ValueError):
            nota_extracao(StatusExtracao.OK)


class TestTextoDefinitivo:
    def test_parcial_acrescenta_nota_ao_texto(self):
        texto = texto_definitivo(StatusExtracao.PARCIAL, "corpo parcial", 1)

        assert texto.startswith("corpo parcial")
        assert "parcial" in texto.lower()

    def test_falha_persiste_apenas_a_nota(self):
        texto = texto_definitivo(StatusExtracao.FALHA, "ignorado")

        assert texto == nota_extracao(StatusExtracao.FALHA)

    def test_protegido_persiste_apenas_a_nota(self):
        texto = texto_definitivo(StatusExtracao.PROTEGIDO, "ignorado")

        assert texto == nota_extracao(StatusExtracao.PROTEGIDO)


class TestResumoDeterministico:
    @pytest.mark.parametrize(
        "status", [StatusExtracao.FALHA, StatusExtracao.PROTEGIDO]
    )
    def test_resumo_e_integro(self, status):
        resumo = resumo_deterministico(status)

        assert resumo_completo(resumo.short_summary, resumo.long_summary)

    def test_parcial_nao_tem_resumo_deterministico(self):
        with pytest.raises(ValueError):
            resumo_deterministico(StatusExtracao.PARCIAL)


class TestItemPendente:
    def test_carrega_status_texto_e_paginas(self):
        item = ItemPendente(object(), StatusExtracao.PARCIAL, "texto", 2)

        assert item.status is StatusExtracao.PARCIAL
        assert item.texto == "texto"
        assert item.paginas_com_falha == 2
