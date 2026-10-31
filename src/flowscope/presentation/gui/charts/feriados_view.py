"""Renderização e seleção da árvore da aba ``Feriados``."""

from __future__ import annotations

import tkinter as tk

from flowscope.application.calendar.view import (
    FeriadoAno,
    FeriadoDia,
    FeriadoMes,
    construir_arvore,
    feriados_do_payload,
    texto_ano,
    texto_dia,
    texto_mes,
)
from flowscope.domain.calendar import Holiday

_VAZIO = "Nenhum feriado em cache. Use o botão de atualização para carregar."
_SEM_SELECAO = "Selecione um ano, mês ou dia para ver os feriados."


class FeriadosViewMixin:
    """Mixin com a montagem da árvore e a atualização do texto."""

    def _load_cache(self: FeriadosViewMixin) -> None:
        if self._service is None:
            self._render({})
            return
        anos: dict[int, tuple[Holiday, ...]] = {}
        for ano in self._service.cached_years():
            holidays = feriados_do_payload(self._service.listar_ano(ano))
            if holidays:
                anos[ano] = holidays
        self._anos = anos
        self._render(anos)

    def _render(
        self: FeriadosViewMixin, anos: dict[int, tuple[Holiday, ...]]
    ) -> None:
        selecionado = self._selected_key()
        self._arvore = construir_arvore(anos)
        self._nos.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)
        for ano in self._arvore:
            self._inserir_ano(ano)
        if not self._arvore:
            self._set_text(_VAZIO)
            return
        if selecionado is not None:
            self._select_key(selecionado)
        else:
            self._set_text(_SEM_SELECAO)

    def _inserir_ano(self: FeriadosViewMixin, ano: FeriadoAno) -> None:
        iid_ano = self._tree.insert("", "end", text=str(ano.ano))
        self._nos[iid_ano] = (ano.ano, None, None)
        for mes in ano.meses:
            iid_mes = self._tree.insert(iid_ano, "end", text=mes.nome)
            self._nos[iid_mes] = (ano.ano, mes.mes, None)
            for dia in mes.dias:
                iid_dia = self._tree.insert(iid_mes, "end", text=dia.rotulo)
                self._nos[iid_dia] = (ano.ano, mes.mes, dia.data.day)

    def _on_select(self: FeriadosViewMixin, _event: object = None) -> None:
        selecao = self._tree.selection()
        if not selecao:
            return
        chave = self._nos.get(selecao[0])
        if chave is not None:
            self._atualizar_texto(chave)

    def _atualizar_texto(
        self: FeriadosViewMixin,
        chave: tuple[int, int | None, int | None],
    ) -> None:
        ano, mes, dia = chave
        feriado_ano = self._buscar_ano(ano)
        if feriado_ano is None:
            self._set_text(_VAZIO)
            return
        if mes is None:
            self._set_text(texto_ano(feriado_ano))
            return
        feriado_mes = self._buscar_mes(feriado_ano, mes)
        if feriado_mes is None:
            self._set_text(_VAZIO)
            return
        if dia is None:
            self._set_text(texto_mes(feriado_mes))
            return
        feriado_dia = self._buscar_dia(feriado_mes, dia)
        self._set_text(texto_dia(feriado_dia) if feriado_dia else _VAZIO)

    def _buscar_ano(self: FeriadosViewMixin, ano: int) -> FeriadoAno | None:
        return next((item for item in self._arvore if item.ano == ano), None)

    @staticmethod
    def _buscar_mes(ano: FeriadoAno, mes: int) -> FeriadoMes | None:
        return next((item for item in ano.meses if item.mes == mes), None)

    @staticmethod
    def _buscar_dia(mes: FeriadoMes, dia: int) -> FeriadoDia | None:
        return next((item for item in mes.dias if item.data.day == dia), None)

    def _set_text(self: FeriadosViewMixin, texto: str) -> None:
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", texto)

    def _selected_key(
        self: FeriadosViewMixin,
    ) -> tuple[int, int | None, int | None] | None:
        selecao = self._tree.selection()
        return self._nos.get(selecao[0]) if selecao else None

    def _select_key(
        self: FeriadosViewMixin,
        chave: tuple[int, int | None, int | None],
    ) -> None:
        for iid, valor in self._nos.items():
            if valor == chave:
                self._tree.selection_set(iid)
                self._tree.see(iid)
                self._atualizar_texto(valor)
                return
        self._set_text(_SEM_SELECAO if self._arvore else _VAZIO)


__all__ = ["FeriadosViewMixin"]
