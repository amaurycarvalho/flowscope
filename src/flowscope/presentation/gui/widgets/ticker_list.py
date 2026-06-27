import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


class TickerList:
    def __init__(self, parent: tk.Widget, on_change: callable = None):
        self.frame = tk.Frame(parent)
        self._on_change = on_change

        tk.Label(self.frame, text="Tickers (um por linha):").pack(anchor=tk.W)

        text_frame = tk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self._text = tk.Text(text_frame, height=15, width=20)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Button(btn_frame, text="Salvar Tickers", command=self._save).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Carregar Tickers", command=self._load).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Filtrar", command=self._filter).pack(side=tk.LEFT, padx=2)

    def set_tickers(self, tickers: list[str]) -> None:
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(tickers))

    def get_tickers(self) -> list[str]:
        content = self._text.get("1.0", tk.END).strip()
        return [t.strip().upper() for t in content.splitlines() if t.strip()]

    def _save(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if path:
            Path(path).write_text("\n".join(self.get_tickers()), encoding="utf-8")

    def _filter(self) -> None:
        if self._on_change:
            self._on_change()

    def _load(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if path and Path(path).exists():
            content = Path(path).read_text(encoding="utf-8")
            self._text.delete("1.0", tk.END)
            self._text.insert("1.0", content)
