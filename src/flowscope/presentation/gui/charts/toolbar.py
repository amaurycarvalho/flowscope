"""Barra de ferramentas personalizada em português para os gráficos do FlowScope."""

import tkinter as tk
from collections.abc import Callable

from matplotlib.backend_bases import _Mode
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from flowscope.presentation.gui.widgets.tooltip import ToolTip as FsToolTip
from flowscope.presentation.main import _resolve_icon_path


class ToolbarBR(NavigationToolbar2Tk):
    """Barra de ferramentas do matplotlib com rótulos em português do Brasil."""

    toolitems = (
        ("Início", "Restaurar visualização original", "home", "home"),
        ("Voltar", "Voltar à visualização anterior", "back", "back"),
        ("Avançar", "Avançar para próxima visualização", "forward", "forward"),
        (None, None, None, None),
        ("Mover", "Botão esquerdo: mover, Botão direito: zoom", "move", "pan"),
        ("Ampliar", "Ampliar região retangular", "zoom_to_rect", "zoom"),
        (None, None, None, None),
        ("Salvar", "Salvar gráfico como imagem", "filesave", "save_figure"),
    )

    def __init__(
        self: "ToolbarBR",
        canvas: FigureCanvasTkAgg,
        parent: tk.Widget,
        *,
        copy_chart_callback: Callable[[Figure], None] | None = None,
    ) -> None:
        """Configura a barra de ferramentas e adiciona o botão de copiar gráfico."""
        self._copy_chart_callback = copy_chart_callback
        super().__init__(canvas, parent)
        self._add_copy_chart_button()

    def _add_copy_chart_button(self: "ToolbarBR") -> None:
        icon = str(_resolve_icon_path("edit-copy.png"))
        btn = self._Button("Copiar Gráfico", icon, False, self.copy_chart)
        FsToolTip(btn, "Copiar gráfico como imagem para a área de transferência")

    def copy_chart(self: "ToolbarBR") -> None:
        """Copia a figura atual do gráfico para a área de transferência."""
        if self._copy_chart_callback:
            self._copy_chart_callback(self.canvas.figure)

    def _update_buttons_checked(self: "ToolbarBR") -> None:
        for text, mode in [("Ampliar", _Mode.ZOOM), ("Mover", _Mode.PAN)]:
            if text in self._buttons:
                if self.mode == mode:
                    self._buttons[text].select()
                else:
                    self._buttons[text].deselect()

    def home(self: "ToolbarBR", *args: object, **kwargs: object) -> None:
        """Restaura a visualização original e desativa o modo de interação ativo."""
        super().home(*args, **kwargs)
        if self.mode != _Mode.NONE:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
            self._update_buttons_checked()

    def pan(self: "ToolbarBR", *args: object, **kwargs: object) -> None:
        """Alterna o modo de mover e desativa o zoom quando ativo."""
        if self.mode == _Mode.ZOOM:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        super().pan(*args, **kwargs)
        self._update_buttons_checked()

    def zoom(self: "ToolbarBR", *args: object, **kwargs: object) -> None:
        """Alterna o modo de ampliar e desativa o mover quando ativo."""
        if self.mode == _Mode.PAN:
            self.mode = _Mode.NONE
            self.canvas.widgetlock.release(self)
        super().zoom(*args, **kwargs)
        self._update_buttons_checked()
