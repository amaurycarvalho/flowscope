import tkinter as tk
import tkinter.ttk as ttk


class OrientationPanel:
    def __init__(self, parent: tk.Widget):
        self.frame = tk.Frame(parent)

        self._title_label = ttk.Label(
            self.frame, font=("TkDefaultFont", 9, "bold")
        )
        self._title_label.pack(anchor=tk.W, pady=(0, 2))

        text_frame = tk.Frame(self.frame)
        self._text = tk.Text(text_frame, height=10, width=40, wrap=tk.WORD)
        self._text.configure(state=tk.DISABLED)
        self._text.tag_config("bold", font=("TkDefaultFont", 9, "bold"))
        self._text.tag_config("italic", font=("TkDefaultFont", 9, "italic"))
        self._scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=self._scrollbar.set)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_frame.pack(fill=tk.X)

        self.set_content("", [])

    def set_content(self, title: str, body: list[tuple[str, str]]) -> None:
        self._title_label.config(text=title)
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        for segment, tag in body:
            self._text.insert("end", segment, tag if tag else ())
        self._text.configure(state=tk.DISABLED)
