"""Vínculo da roda do mouse à rolagem vertical de um widget."""

import tkinter as tk


def passo_da_roda(event: object) -> int:
    """Calcula o passo de rolagem de um evento de roda (-1 acima, 1 abaixo)."""
    numero = getattr(event, "num", None)
    delta = getattr(event, "delta", 0)
    if numero == 4:
        return -1
    if numero == 5:
        return 1
    return -1 if delta > 0 else 1


def vincular_roda(widget: tk.Widget, alvo: tk.Widget) -> None:
    """Faz a roda do mouse sobre ``widget`` rolar ``alvo`` verticalmente."""

    def _on_wheel(event: object) -> str:
        alvo.yview_scroll(passo_da_roda(event), "units")
        return "break"

    widget.bind("<MouseWheel>", _on_wheel, add="+")
    widget.bind("<Button-4>", _on_wheel, add="+")
    widget.bind("<Button-5>", _on_wheel, add="+")
