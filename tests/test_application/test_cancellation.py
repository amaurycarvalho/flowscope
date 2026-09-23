import pytest

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)


class TestCancellationToken:
    def test_inicia_sem_cancelamento(self):
        token = CancellationToken()
        assert token.is_set is False
        token.raise_if_cancelled()

    def test_solicitar_marca_cancelado(self):
        token = CancellationToken()
        token.request()
        assert token.is_set is True

    def test_limpar_remove_solicitacao(self):
        token = CancellationToken()
        token.request()
        token.clear()
        assert token.is_set is False
        token.raise_if_cancelled()

    def test_raise_if_cancelled_lanca_apos_solicitacao(self):
        token = CancellationToken()
        token.request()
        with pytest.raises(OperacaoCancelada):
            token.raise_if_cancelled()
