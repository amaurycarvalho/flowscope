"""Testes da segurança de expressão regular do chat."""

import pytest

from flowscope.application.chat.seguranca_regex import (
    PadraoBloqueado,
    PadraoInvalido,
    compilar,
)


class TestCompilacao:
    def test_padrao_valido_casa(self) -> None:
        assert compilar("PETR4").buscar("[PETR4] PL=3.2") is True
        assert compilar("XXXX").buscar("[PETR4] PL=3.2") is False

    def test_backreference_bloqueada(self) -> None:
        with pytest.raises(PadraoBloqueado):
            compilar(r"(a)\1")

    def test_quantificador_aninhado_bloqueado(self) -> None:
        with pytest.raises(PadraoBloqueado):
            compilar("(a+)+")

    def test_repeticao_solta_bloqueada(self) -> None:
        with pytest.raises(PadraoBloqueado):
            compilar(".*.*x")

    def test_padrao_invalido(self) -> None:
        with pytest.raises(PadraoInvalido):
            compilar("(")
