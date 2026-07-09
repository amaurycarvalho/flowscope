from flowscope.application.operation_guard import OperationGuard


class TestOperationGuard:
    def test_acquire_quando_livre_retorna_true(self):
        guard = OperationGuard()
        with guard.acquire() as acquired:
            assert acquired is True

    def test_acquire_quando_ocupado_retorna_false(self):
        guard = OperationGuard()
        with guard.acquire() as outer:
            assert outer is True
            with guard.acquire() as inner:
                assert inner is False

    def test_volta_a_true_apos_liberacao(self):
        guard = OperationGuard()
        with guard.acquire() as first:
            assert first is True
        with guard.acquire() as second:
            assert second is True

    def test_is_busy_retorna_true_quando_ocupado(self):
        guard = OperationGuard()
        with guard.acquire():
            assert guard.is_busy is True

    def test_is_busy_retorna_false_quando_livre(self):
        guard = OperationGuard()
        assert guard.is_busy is False
        with guard.acquire():
            pass
        assert guard.is_busy is False
