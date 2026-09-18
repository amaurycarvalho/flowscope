"""Rate limiter de janela deslizante para chamadas de LLM.

Limita o número de chamadas por minuto (RPM), enfileirando as excedentes em
vez de falharem. É seguro para uso concorrente e usa relógio e função de sono
injetáveis para facilitar os testes.
"""

import threading
import time
from collections import deque
from collections.abc import Callable

#: RPM padrão quando nenhum é informado.
DEFAULT_RPM = 5

#: Tamanho da janela deslizante, em segundos.
WINDOW_SECONDS = 60.0


class RateLimiter:
    """Limitador de taxa por janela deslizante, thread-safe."""

    def __init__(
        self: "RateLimiter",
        rpm: int = DEFAULT_RPM,
        *,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        """Configura o limite e injeta relógio/função de sono opcionais."""
        self._rpm = max(1, int(rpm))
        self._clock = clock or time.monotonic
        self._sleeper = sleeper or time.sleep
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    @property
    def rpm(self: "RateLimiter") -> int:
        """Número máximo de chamadas permitidas por janela."""
        return self._rpm

    def acquire(self: "RateLimiter") -> None:
        """Bloqueia até que uma chamada seja permitida na janela atual."""
        while True:
            with self._lock:
                now = self._clock()
                self._evict(now)
                if len(self._timestamps) < self._rpm:
                    self._timestamps.append(now)
                    return
                espera = self._timestamps[0] + WINDOW_SECONDS - now
            if espera > 0:
                self._sleeper(espera)

    def _evict(self: "RateLimiter", now: float) -> None:
        """Descarta timestamps que já saíram da janela deslizante."""
        limite = now - WINDOW_SECONDS
        while self._timestamps and self._timestamps[0] <= limite:
            self._timestamps.popleft()
