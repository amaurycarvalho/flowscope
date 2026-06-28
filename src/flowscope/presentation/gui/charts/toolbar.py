from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

from flowscope.presentation.gui.widgets.tooltip import ToolTip as FsToolTip
from flowscope.presentation.main import _resolve_icon_path


class ToolbarBR(NavigationToolbar2Tk):
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

    def __init__(self, canvas, parent, *, copy_chart_callback=None):
        self._copy_chart_callback = copy_chart_callback
        super().__init__(canvas, parent)
        self._add_copy_chart_button()

    def _add_copy_chart_button(self):
        icon = str(_resolve_icon_path("edit-copy.png"))
        btn = self._Button("Copiar Gráfico", icon, False, self.copy_chart)
        FsToolTip(btn, "Copiar gráfico como imagem para a área de transferência")

    def copy_chart(self):
        if self._copy_chart_callback:
            self._copy_chart_callback(self.canvas.figure)
