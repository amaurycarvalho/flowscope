"""Testes da comparação semântica de versões."""

from flowscope.domain.version import is_newer, parse_version


class TestParseVersion:
    def test_tres_segmentos(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_prefixo_v(self):
        assert parse_version("v1.2.3") == (1, 2, 3)

    def test_prefixo_v_maiusculo(self):
        assert parse_version("V10.0.1") == (10, 0, 1)

    def test_espacos_ao_redor(self):
        assert parse_version("  v1.2.0  ") == (1, 2, 0)

    def test_texto_invalido(self):
        assert parse_version("abc") is None

    def test_segmento_nao_numerico(self):
        assert parse_version("1.x.3") is None

    def test_menos_de_tres_segmentos(self):
        assert parse_version("1.2") is None

    def test_mais_de_tres_segmentos(self):
        assert parse_version("1.2.3.4") is None

    def test_sufixo_de_pre_lancamento(self):
        assert parse_version("1.2.0-rc1") is None

    def test_entrada_nao_string(self):
        assert parse_version(None) is None


class TestIsNewer:
    def test_publicada_mais_nova(self):
        assert is_newer("1.2.0", "1.1.0") is True

    def test_publicada_igual(self):
        assert is_newer("1.1.0", "1.1.0") is False

    def test_publicada_anterior(self):
        assert is_newer("1.0.0", "1.1.0") is False

    def test_prefixo_v(self):
        assert is_newer("v1.2.0", "1.1.0") is True

    def test_publicada_invalida(self):
        assert is_newer("abc", "1.1.0") is False

    def test_atual_invalida(self):
        assert is_newer("1.2.0", "abc") is False

    def test_comparacao_numerica_e_nao_lexical(self):
        assert is_newer("1.10.0", "1.9.0") is True
