from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.axes import Axes


def create_empty(fig: Figure, axes: list[Axes]) -> Text:
    label = fig.text(
        0.5, 0.5, "Sem dados",
        ha="center", va="center", fontsize=14, color="lightgray",
    )
    for ax in axes:
        ax.axis("off")
    return label


def show_empty(fig: Figure, axes: list[Axes], label: Text) -> None:
    for ax in axes:
        ax.clear()
        ax.axis("off")
    label.set_visible(True)


def hide_empty(label: Text) -> None:
    label.set_visible(False)
