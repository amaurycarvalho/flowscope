"""Campo de texto somente-leitura com cursor visível e atalhos de cópia.

Mantém o widget editável para exibir cursor de foco e permitir seleção, mas
intercepta as teclas que alterariam o conteúdo. Navegação, Shift+setas,
Ctrl+A e Ctrl+C continuam funcionando; colar e recortar são bloqueados.
"""

import tkinter as tk

#: Teclas de navegação que permanecem funcionais no campo.
_TECLAS_NAVEGACAO = frozenset(
    {
        "Left",
        "Right",
        "Up",
        "Down",
        "Home",
        "End",
        "Prior",
        "Next",
        "KP_Left",
        "KP_Right",
        "KP_Up",
        "KP_Down",
        "KP_Home",
        "KP_End",
        "KP_Prior",
        "KP_Next",
    }
)

#: Máscara do modificador Control nos eventos do Tk.
_MASCARA_CONTROL = 0x4


class ReadonlyText(tk.Text):
    """``tk.Text`` que bloqueia edição preservando seleção e cursor."""

    def __init__(self: "ReadonlyText", master: tk.Misc, **kwargs: object) -> None:
        """Configura a largura do cursor e instala os bloqueios de edição."""
        kwargs.setdefault("insertwidth", 2)
        super().__init__(master, **kwargs)
        self.bind("<Key>", self._on_key)
        self.bind("<Control-Key-a>", self._selecionar_tudo)
        self.bind("<Control-Key-A>", self._selecionar_tudo)
        self.bind("<<Paste>>", lambda _event: "break")
        self.bind("<<Cut>>", lambda _event: "break")
        self.bind("<<PasteSelection>>", lambda _event: "break")

    def _on_key(self: "ReadonlyText", event: tk.Event) -> str | None:
        """Permite navegação e cópia; bloqueia qualquer tecla que edite."""
        if event.keysym in _TECLAS_NAVEGACAO:
            return None
        if event.state & _MASCARA_CONTROL and event.keysym.lower() in ("a", "c"):
            return None
        return "break"

    def _selecionar_tudo(self: "ReadonlyText", event: tk.Event | None = None) -> str:
        """Seleciona todo o conteúdo, cobrindo o atalho ausente no X11."""
        self.tag_add("sel", "1.0", "end-1c")
        self.mark_set("insert", "1.0")
        self.see("1.0")
        return "break"
