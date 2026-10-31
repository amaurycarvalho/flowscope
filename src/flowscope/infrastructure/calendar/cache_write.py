"""Escrita atômica e housekeeping do cache do calendário."""

from __future__ import annotations

import json

from flowscope.application.calendar.ports import YearHolidays
from flowscope.infrastructure.action_lock import ActionLock, OperacaoEmAndamento
from flowscope.infrastructure.calendar.housekeeping import run_housekeeping
from flowscope.infrastructure.calendar.storage import encode_year
from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes

_LOCK_WAIT_SECONDS = 5.0


class HolidayCacheWriteMixin:
    """Mixin com gravação atômica e housekeeping sob lock dedicado."""

    def write(
        self: HolidayCacheWriteMixin,
        data: YearHolidays,
        reuse_fresh: bool = True,
    ) -> YearHolidays | None:
        """Write one year atomically and reuse a fresher concurrent result."""
        lock = ActionLock(caminho=self.lock_path)
        try:
            lock.adquirir(esperar=_LOCK_WAIT_SECONDS)
        except OperacaoEmAndamento:
            return self.read(data.year)
        try:
            self.holidays_dir.mkdir(parents=True, exist_ok=True)
            existing = self.read(data.year)
            if (
                reuse_fresh
                and existing is not None
                and self.is_fresh(data.year)
                and existing.fetched_at != data.fetched_at
                and (existing.published or not data.published)
            ):
                return existing
            ttl = (
                data.ttl_seconds
                if data.ttl_seconds is not None
                else self._ttl(data, self._local_date())
            )
            payload = encode_year(data, ttl)
            _atomic_write_bytes(
                self.path(data.year),
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )
            return data
        finally:
            lock.liberar()

    def housekeeping(
        self: HolidayCacheWriteMixin,
        reference_year: int,
        protected_years: tuple[int, ...] = (),
    ) -> None:
        """Remove files outside the retention window under the same lock."""
        lock = ActionLock(caminho=self.lock_path)
        try:
            lock.adquirir(esperar=_LOCK_WAIT_SECONDS)
        except OperacaoEmAndamento:
            return
        try:
            run_housekeeping(
                self.holidays_dir,
                reference_year,
                protected_years=protected_years,
            )
        finally:
            lock.liberar()


__all__ = ["HolidayCacheWriteMixin"]
