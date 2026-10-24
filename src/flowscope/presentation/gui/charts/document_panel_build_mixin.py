"""Construção dos widgets do painel de documentos."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from flowscope.presentation.gui.charts.document_tree_view import DocumentTreeView
from flowscope.presentation.gui.llm.model_selector import SeletorModelo
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText
from flowscope.presentation.gui.widgets.tooltip import ToolTip


class DocumentPanelBuildMixin:
    """Constrói toolbar, árvore e pré-visualização do painel."""

    def _build_toolbar(self: DocumentPanelBuildMixin) -> None:
        """Constrói a barra com os controles de atualizar e abrir."""
        barra = tk.Frame(self.frame)
        barra.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))
        self._refresh_btn = ttk.Button(
            barra, text="Atualizar", command=self._on_refresh
        )
        self._refresh_btn.pack(side=tk.LEFT, padx=2)
        self._open_btn = ttk.Button(
            barra, text="Abrir documento", command=self._on_open_selected,
            state=tk.DISABLED,
        )
        self._open_btn.pack(side=tk.LEFT, padx=2)
        self._model_selector = SeletorModelo(
            barra,
            config_port=self._config_port,
            on_config=self._on_configurar,
            on_changed=self._on_model_changed,
        )
        self._model_selector.pack(side=tk.LEFT, padx=2)
        self._resumir_btn = ttk.Button(
            barra, text="Resumir pendentes", command=self._on_resumir,
            state=tk.DISABLED,
        )
        self._resumir_btn.pack(side=tk.LEFT, padx=2)
        ToolTip(self._refresh_btn, "Atualizar a lista de documentos em cache")
        ToolTip(self._open_btn, "Abrir o documento selecionado no aplicativo padrão")
        ToolTip(self._resumir_btn, "Resumir os documentos pendentes com a I.A.")

    def _build_container(self: DocumentPanelBuildMixin) -> None:
        """Constrói a área de conteúdo com a árvore e a pré-visualização."""
        self._container = tk.Frame(self.frame)
        self._container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._content = tk.PanedWindow(
            self._container, orient=tk.HORIZONTAL,
            sashrelief=tk.RAISED, sashwidth=6,
        )
        self._view = DocumentTreeView(self._content)
        self._tree = self._view.tree
        self._itens = self._view.itens
        self._grupos = self._view.grupos
        self._por_caminho = self._view.por_caminho
        self._guidances_folhas = self._view.guidances
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Button-1>", self._on_click)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Return>", self._on_double_click)
        self._content.add(self._view.frame, stretch="always")
        self._content.add(self._build_preview(), stretch="always")
        self._content.pack(fill=tk.BOTH, expand=True)
        self._empty_label = tk.Label(
            self._container, text="", fg="gray", justify=tk.CENTER,
        )

    def _build_preview(self: DocumentPanelBuildMixin) -> tk.Frame:
        """Constrói a caixa de texto somente-leitura da pré-visualização."""
        quadro = tk.Frame(self._content)
        self._preview = ReadonlyText(quadro, wrap=tk.WORD, padx=8, pady=8)
        self._preview_scrollbar = ttk.Scrollbar(
            quadro, orient=tk.VERTICAL, command=self._preview.yview
        )
        self._preview.configure(yscrollcommand=self._preview_scrollbar.set)
        self._preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._preview.bind("<Double-1>", self._on_preview_double_click)
        vincular_roda(self._preview, self._preview)
        return quadro
