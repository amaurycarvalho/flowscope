"""Aba ``Feriados``: árvore ano/mês/dia e texto somente leitura."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from datetime import date
from tkinter import ttk

from flowscope.application.calendar.service import CalendarService
from flowscope.presentation.gui.charts.feriados_refresh import FeriadosRefreshMixin
from flowscope.presentation.gui.charts.feriados_view import FeriadosViewMixin
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText


class FeriadosPanel(FeriadosRefreshMixin, FeriadosViewMixin):
    """Painel de consulta do calendário de feriados, sem rede na montagem."""

    def __init__(
        self: FeriadosPanel,
        parent: tk.Widget,
        *,
        service: CalendarService | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        icon_loader: Callable[[str], object] | None = None,
        today: Callable[[], date] | None = None,
    ) -> None:
        """Build the panel and load the tree from the local cache."""
        self.frame = ttk.Frame(parent)
        self._service = service
        self._status = status_callback
        self._icon_loader = icon_loader
        self._today = today or date.today
        self._anos: dict[int, tuple] = {}
        self._arvore: tuple = ()
        self._nos: dict[str, tuple[int, int | None, int | None]] = {}
        self._refreshing = False
        self._icon_refresh = self._load_icon("view-refresh.png")
        self._icon_loading = self._load_icon("content-loading.png")
        self._build()
        self._load_cache()

    def _load_icon(self: FeriadosPanel, nome: str) -> object | None:
        if self._icon_loader is None:
            return None
        try:
            return self._icon_loader(nome)
        except Exception:
            return None

    def _build(self: FeriadosPanel) -> None:
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, padx=4, pady=4)
        self._refresh_button = tk.Button(
            toolbar,
            text="Atualizar",
            image=self._icon_refresh,
            command=self.refresh,
            cursor="hand2",
            padx=0,
        )
        self._refresh_button.pack(side=tk.LEFT)

        painel = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        painel.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        tree_frame = ttk.Frame(painel)
        self._tree = ttk.Treeview(
            tree_frame, show="tree", selectmode="browse"
        )
        barra = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self._tree.yview
        )
        self._tree.configure(yscrollcommand=barra.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        painel.add(tree_frame, weight=1)

        text_frame = ttk.Frame(painel)
        self._text = ReadonlyText(text_frame, wrap="word", width=60, height=20)
        barra_texto = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self._text.yview
        )
        self._text.configure(yscrollcommand=barra_texto.set)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra_texto.pack(side=tk.RIGHT, fill=tk.Y)
        painel.add(text_frame, weight=2)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._set_text(
            "Nenhum feriado em cache. Use o botão de atualização para carregar."
        )


__all__ = ["FeriadosPanel"]
