import tkinter as tk
import tkinter.ttk as ttk


class OrientationPanel:
    def __init__(self, parent: tk.Widget):
        self.frame = tk.Frame(parent)

        self._title_label = ttk.Label(
            self.frame, font=("TkDefaultFont", 9, "bold")
        )
        self._title_label.pack(anchor=tk.W, pady=(0, 2))

        self._text = tk.Text(self.frame, height=10, width=40, wrap=tk.WORD)
        self._text.configure(state=tk.DISABLED)
        self._text.pack(fill=tk.X)

        self.set_content("", "")

    def set_content(self, title: str, body: str) -> None:
        self._title_label.config(text=title)
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", body)
        self._text.configure(state=tk.DISABLED)
