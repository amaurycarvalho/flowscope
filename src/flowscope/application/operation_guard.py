from contextlib import contextmanager


class OperationGuard:
    def __init__(self):
        self._busy = False

    @contextmanager
    def acquire(self):
        if self._busy:
            yield False
            return
        self._busy = True
        try:
            yield True
        finally:
            self._busy = False

    @property
    def is_busy(self) -> bool:
        return self._busy
