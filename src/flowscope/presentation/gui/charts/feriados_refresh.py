"""Atualização em background da aba ``Feriados``."""

from __future__ import annotations

import threading
import tkinter as tk

from flowscope.application.calendar.view import feriados_do_payload


class FeriadosRefreshMixin:
    """Mixin com o ciclo de atualização forçada do calendário."""

    def refresh(self: FeriadosRefreshMixin) -> None:
        """Force revalidation of displayed years in a background thread."""
        if self._refreshing:
            return
        anos = sorted(self._anos) or [self._today().year]
        self._set_refreshing(True)
        threading.Thread(
            target=self._worker, args=(anos,), daemon=True
        ).start()

    def _worker(self: FeriadosRefreshMixin, anos: list[int]) -> None:
        try:
            payloads = {}
            for ano in anos:
                self._service.ensure_year(ano, force=True)
                payloads[ano] = self._service.listar_ano(ano)
        except Exception as exc:
            self.frame.after(0, lambda erro=exc: self._finish(None, erro))
            return
        self.frame.after(0, lambda: self._finish(payloads, None))

    def _finish(
        self: FeriadosRefreshMixin,
        payloads: dict[int, dict] | None,
        erro: Exception | None,
    ) -> None:
        self._set_refreshing(False)
        if erro is not None:
            self._status_message("Falha ao atualizar feriados", "⚠")
            return
        if payloads is None:
            return
        estados = [payload.get("estado") for payload in payloads.values()]
        if all(estado == "calendario_indisponivel" for estado in estados):
            self._status_message("Calendário indisponível", "⚠")
            return
        self._render_payloads(payloads)
        self._status_after(estados)

    def _render_payloads(self: FeriadosRefreshMixin, payloads: dict[int, dict]) -> None:
        anos = {
            ano: feriados_do_payload(payload)
            for ano, payload in payloads.items()
        }
        self._anos = {ano: holidays for ano, holidays in anos.items() if holidays}
        self._render(self._anos)

    def _status_after(self: FeriadosRefreshMixin, estados: list[object]) -> None:
        if any(estado == "defasado" for estado in estados):
            self._status_message("Calendário defasado", "⚠")
        else:
            self._status_message("Feriados atualizados", "✓")

    def _set_refreshing(self: FeriadosRefreshMixin, valor: bool) -> None:
        self._refreshing = valor
        self._refresh_button.config(state=tk.DISABLED if valor else tk.NORMAL)
        if self._icon_refresh is not None:
            self._refresh_button.config(
                image=self._icon_loading if valor else self._icon_refresh
            )
        else:
            self._refresh_button.config(
                text="Atualizando..." if valor else "Atualizar"
            )

    def _status_message(self: FeriadosRefreshMixin, mensagem: str, icone: str) -> None:
        if self._status is not None:
            self._status(mensagem, icone)


__all__ = ["FeriadosRefreshMixin"]
