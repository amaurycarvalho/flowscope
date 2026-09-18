"""Testes do rate limiter de janela deslizante."""

import threading

import pytest

from flowscope.infrastructure.llm.rate_limiter import DEFAULT_RPM, RateLimiter

pytestmark = pytest.mark.llm


class _FakeClock:
    """Relógio monotônico falso cujo sono avança o tempo."""

    def __init__(self: "_FakeClock") -> None:
        self.t = 0.0
        self.sonos: list[float] = []

    def now(self: "_FakeClock") -> float:
        return self.t

    def sleep(self: "_FakeClock", segundos: float) -> None:
        self.sonos.append(segundos)
        self.t += segundos


def _limiter(rpm: int, relogio: _FakeClock) -> RateLimiter:
    return RateLimiter(rpm, clock=relogio.now, sleeper=relogio.sleep)


class TestRateLimiter:
    def test_rpm_padrao_e_cinco(self):
        assert RateLimiter().rpm == DEFAULT_RPM == 5

    def test_rpm_customizado(self):
        assert RateLimiter(15).rpm == 15

    def test_sob_o_limite_nao_espera(self):
        relogio = _FakeClock()
        limiter = _limiter(5, relogio)
        for _ in range(5):
            limiter.acquire()
        assert relogio.sonos == []
        assert relogio.t == 0.0

    def test_excedente_aguarda_nova_janela(self):
        relogio = _FakeClock()
        limiter = _limiter(2, relogio)
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        assert relogio.sonos == [60.0]
        assert relogio.t == 60.0

    def test_janela_libera_apos_espera(self):
        relogio = _FakeClock()
        limiter = _limiter(1, relogio)
        limiter.acquire()
        relogio.t = 30.0
        limiter.acquire()
        assert relogio.sonos == [30.0]

    def test_concorrencia_nao_excede_o_limite(self):
        class _SharedClock:
            def __init__(self):
                self.t = 0.0
                self._lock = threading.Lock()

            def now(self):
                with self._lock:
                    return self.t

            def sleep(self, segundos):
                with self._lock:
                    self.t += segundos

        relogio = _SharedClock()
        limiter = RateLimiter(
            3, clock=relogio.now, sleeper=relogio.sleep
        )
        resultados: list[bool] = []
        trava = threading.Lock()

        def _usar() -> None:
            limiter.acquire()
            with trava:
                resultados.append(True)

        threads = [threading.Thread(target=_usar) for _ in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert len(resultados) == 12
        assert len(limiter._timestamps) <= 3
