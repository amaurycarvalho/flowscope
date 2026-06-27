import tkinter as tk
from tkinter import filedialog
from pathlib import Path


class TickerList:
    def __init__(self, parent: tk.Widget, on_change: callable = None):
        self.frame = tk.Frame(parent)
        self._on_change = on_change

        top_frame = tk.Frame(self.frame)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Tickers (um por linha):").pack(side=tk.LEFT, anchor=tk.W)
        self._counter_label = tk.Label(top_frame, text="", fg="gray")
        self._counter_label.pack(side=tk.RIGHT, padx=4)

        text_frame = tk.Frame(self.frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self._text = tk.Text(text_frame, height=15, width=20)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._text.bind("<Double-Button-1>", self._on_double_click)
        self._text.bind("<Button-3>", self._show_context_menu)

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        tk.Button(btn_frame, text="Salvar Tickers", command=self._save, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Carregar Tickers", command=self._load, cursor="hand2").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Filtrar", command=self._filter, cursor="hand2").pack(side=tk.LEFT, padx=2)

        self._context_menu = tk.Menu(self.frame, tearoff=0)
        self._context_menu.add_command(label="Copiar ticker", command=self._copy_selected_ticker)
        self._context_menu.add_command(label="Remover do filtro", command=self._remove_selected_ticker)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Selecionar todos", command=self._select_all)
        self._context_menu.add_command(label="Limpar seleção", command=self._clear_selection)

    def set_counter(self, text: str) -> None:
        self._counter_label.config(text=text)

    def set_tickers(self, tickers: list[str]) -> None:
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(tickers))

    def get_tickers(self) -> list[str]:
        content = self._text.get("1.0", tk.END).strip()
        return [t.strip().upper() for t in content.splitlines() if t.strip()]

    def _on_double_click(self, event):
        try:
            index = self._text.index(f"@{event.x},{event.y}")
            line_start = self._text.index(f"{index} linestart")
            line_end = self._text.index(f"{index} lineend")
            ticker = self._text.get(line_start, line_end).strip()
            if ticker:
                self._text.delete("1.0", tk.END)
                self._text.insert("1.0", ticker)
                self._filter()
        except tk.TclError:
            pass

    def _show_context_menu(self, event):
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _copy_selected_ticker(self):
        try:
            sel = self._text.tag_ranges(tk.SEL)
            if sel:
                text = self._text.get(sel[0], sel[1])
            else:
                cursor = self._text.index(tk.INSERT)
                word_start = self._text.index(f"{cursor} wordstart")
                word_end = self._text.index(f"{cursor} wordend")
                text = self._text.get(word_start, word_end)
            self._text.clipboard_clear()
            self._text.clipboard_append(text.strip())
        except tk.TclError:
            pass

    def _remove_selected_ticker(self):
        try:
            sel = self._text.tag_ranges(tk.SEL)
            if sel:
                self._text.delete(sel[0], sel[1])
                self._filter()
        except tk.TclError:
            pass

    def _select_all(self):
        self._text.tag_add(tk.SEL, "1.0", tk.END)

    def _clear_selection(self):
        self._text.tag_remove(tk.SEL, "1.0", tk.END)

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
