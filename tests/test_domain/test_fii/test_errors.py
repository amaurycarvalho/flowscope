"""Testes da exceção de domínio de ticker não encontrado."""

import flowscope.domain.fii as dominio
from flowscope.domain.fii import TickerNaoEncontrado


class TestTickerNaoEncontrado:
    def test_exportada_pelo_pacote_de_dominio(self):
        assert dominio.TickerNaoEncontrado is TickerNaoEncontrado
        assert "TickerNaoEncontrado" in dominio.__all__

    def test_e_excecao(self):
        assert issubclass(TickerNaoEncontrado, Exception)
