from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk


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
