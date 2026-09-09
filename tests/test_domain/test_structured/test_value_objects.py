import pytest

from flowscope.domain.structured import (
    CategoriaDocumento,
    CategoriaMaterialFact,
    CodeCVM,
)


class TestCodeCVM:
    def test_armazena_valor_numerico(self):
        codigo = CodeCVM("9512")
        assert codigo.value == "9512"

    def test_str_retorna_valor(self):
        assert str(CodeCVM("9512")) == "9512"

    def test_aceita_zeros_a_esquerda(self):
        assert CodeCVM("009512").value == "009512"

    def test_normaliza_espacos(self):
        assert CodeCVM(" 9512 ").value == "9512"

    def test_valor_nao_numerico_lanca_value_error(self):
        with pytest.raises(ValueError):
            CodeCVM("PETR4")

    def test_valor_vazio_lanca_value_error(self):
        with pytest.raises(ValueError):
            CodeCVM("")

    def test_valor_muito_longo_lanca_value_error(self):
        with pytest.raises(ValueError):
            CodeCVM("1234567")

    def test_igualdade_por_valor(self):
        assert CodeCVM("9512") == CodeCVM("9512")
        assert CodeCVM("9512") != CodeCVM("9513")

    def test_hash_por_valor(self):
        assert hash(CodeCVM("9512")) == hash(CodeCVM("9512"))


class TestCategoriaMaterialFact:
    def test_cinco_membros(self):
        assert len(list(CategoriaMaterialFact)) == 5

    def test_membros_com_codigos_esperados(self):
        assert CategoriaMaterialFact.ASSEMBLEIAS.value == "1"
        assert CategoriaMaterialFact.AVISO_ACIONISTAS.value == "3"
        assert CategoriaMaterialFact.FATOS_RELEVANTES.value == "4"
        assert CategoriaMaterialFact.AVISO_DEBENTURISTAS.value == "48"
        assert CategoriaMaterialFact.RELATORIO_PROVENTOS.value == "107"

    def test_iteracao_produz_codigos(self):
        codigos = [categoria.value for categoria in CategoriaMaterialFact]
        assert codigos == ["1", "3", "4", "48", "107"]

    def test_codigo_invalido_rejeitado(self):
        with pytest.raises(ValueError):
            CategoriaMaterialFact("99")

    def test_str_retorna_codigo(self):
        assert str(CategoriaMaterialFact.FATOS_RELEVANTES) == "4"

    def test_categoria_documento_e_alias(self):
        assert CategoriaDocumento is CategoriaMaterialFact
        assert CategoriaDocumento.ASSEMBLEIAS == CategoriaMaterialFact.ASSEMBLEIAS
