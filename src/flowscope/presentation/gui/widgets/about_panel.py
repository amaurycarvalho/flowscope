"""Painel rolável da aba "Sobre" com informações institucionais e atalhos."""

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from flowscope import __release_date__, __version__
from flowscope.presentation.gui.app_constants import PAD, PAD_LARGE, PAD_SMALL
from flowscope.presentation.gui.widgets.mousewheel import vincular_roda

#: Texto de apresentação derivado da seção de descrição do README.md.
APRESENTACAO = (
    "O FlowScope é uma ferramenta open source de análise quantitativa de fluxo "
    "de ordens baseada nos dados públicos consolidados de negociações "
    "disponibilizados pela bolsa de valores B3. Desenvolvido em Python, oferece "
    "interface gráfica (GUI) e linha de comando (CLI), com suporte "
    "multiplataforma para Linux, Windows e macOS."
)

#: Licença de software livre declarada no projeto.
LICENCA = "Software livre e de código aberto (GNU GPLv3)"

#: Endereço do repositório oficial do projeto.
REPOSITORIO_URL = "https://github.com/amaurycarvalho/flowscope"


class AboutPanel:
    """Conteúdo rolável da aba "Sobre" com informações e atalhos."""

    def __init__(
        self: "AboutPanel",
        parent: tk.Widget,
        *,
        icon: object | None = None,
        on_open_repository: Callable[[], None] | None = None,
        on_open_log: Callable[[], None] | None = None,
    ) -> None:
        """Constrói o painel rolável e os seus controles."""
        self._icon = icon
        self._on_open_repository = on_open_repository
        self._on_open_log = on_open_log
        self._presentation_label: tk.Label | None = None
        self._update_area: tk.Frame | None = None

        self.frame = tk.Frame(parent)
        self._canvas = tk.Canvas(self.frame, highlightthickness=0)
        self._content = tk.Frame(self._canvas)
        self._window = self._canvas.create_window(
            (0, 0), window=self._content, anchor="nw"
        )
        scrollbar = ttk.Scrollbar(
            self.frame, orient=tk.VERTICAL, command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._content.bind("<Configure>", self._on_content_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        vincular_roda(self._canvas, self._canvas)
        vincular_roda(self._content, self._canvas)

        self._build_content()

    def _on_content_configure(self: "AboutPanel", _event: object) -> None:
        """Ajusta a região rolável ao tamanho do conteúdo."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self: "AboutPanel", event: tk.Event) -> None:
        """Ajusta a largura do conteúdo e o rebobinamento do texto."""
        self._canvas.itemconfigure(self._window, width=event.width)
        if self._presentation_label is not None:
            self._presentation_label.configure(
                wraplength=max(event.width - PAD * 3, 120)
            )

    def _build_content(self: "AboutPanel") -> None:
        """Monta, na ordem, as informações institucionais e os atalhos."""
        container = tk.Frame(self._content)
        container.pack(fill=tk.BOTH, expand=True, padx=PAD_LARGE, pady=PAD_LARGE)

        if self._icon is not None:
            tk.Label(container, image=self._icon).pack(
                anchor=tk.CENTER, pady=(0, PAD)
            )

        tk.Label(
            container,
            text=f"FlowScope v{__version__}",
            font=("TkDefaultFont", 14, "bold"),
        ).pack(anchor=tk.CENTER, pady=(0, PAD))

        tk.Label(container, text=__release_date__).pack(
            anchor=tk.CENTER, pady=(0, PAD_SMALL)
        )

        tk.Label(container, text=LICENCA).pack(anchor=tk.CENTER, pady=(0, PAD))

        self._presentation_label = tk.Label(
            container,
            text=APRESENTACAO,
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=480,
        )
        self._presentation_label.pack(fill=tk.X, pady=(0, PAD_LARGE))

        botoes = tk.Frame(container)
        botoes.pack(anchor=tk.CENTER)
        tk.Button(
            botoes,
            text="Repositório no GitHub",
            command=self._on_open_repository,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=(0, PAD))
        tk.Button(
            botoes,
            text="Abrir log da aplicação",
            command=self._on_open_log,
            cursor="hand2",
        ).pack(side=tk.LEFT)

        self._update_area = tk.Frame(container)
        self._update_area.pack(fill=tk.X, pady=(PAD_LARGE, 0))

    def show_update(
        self: "AboutPanel",
        versao: str,
        on_open_release: Callable[[], None] | None,
    ) -> None:
        """Exibe, ao final do conteúdo, o aviso e o atalho para a release."""
        if self._update_area is None:
            return
        for filho in self._update_area.winfo_children():
            filho.destroy()
        tk.Label(
            self._update_area,
            text=f"Nova versão v{versao} disponível",
            fg="#8a6d00",
            font=("TkDefaultFont", 10, "bold"),
        ).pack(anchor=tk.CENTER)
        tk.Button(
            self._update_area,
            text="Abrir página da release",
            command=on_open_release,
            cursor="hand2",
        ).pack(anchor=tk.CENTER, pady=(PAD_SMALL, 0))
