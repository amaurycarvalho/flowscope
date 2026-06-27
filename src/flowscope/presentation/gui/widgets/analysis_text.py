import tkinter as tk


class AnalysisText:
    def __init__(self, parent: tk.Widget):
        self.frame = tk.Frame(parent)

        tk.Label(self.frame, text="Análise automática:").pack(anchor=tk.W)

        self._text = tk.Text(self.frame, height=6, width=40, wrap=tk.WORD)
        self._text.insert("1.0", "Análise automática será implementada em versão futura.")
        self._text.configure(state=tk.DISABLED)
        self._text.pack(fill=tk.X)
