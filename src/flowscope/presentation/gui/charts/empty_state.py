"""Estado vazio para as figuras dos gráficos da interface do FlowScope."""

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text


def create_empty(fig: Figure, axes: list[Axes]) -> Text:
    """Cria o rótulo de estado vazio e desativa os eixos da figura."""
    label = fig.text(
        0.5, 0.5, "Sem dados",
        ha="center", va="center", fontsize=14, color="lightgray",
    )
    for ax in axes:
        ax.axis("off")
    return label


def show_empty(fig: Figure, axes: list[Axes], label: Text) -> None:
    """Limpa os eixos e exibe o rótulo de estado vazio na figura."""
    for ax in axes:
        ax.clear()
        ax.axis("off")
    label.set_visible(True)


def hide_empty(label: Text) -> None:
    """Oculta o rótulo de estado vazio da figura."""
    label.set_visible(False)
