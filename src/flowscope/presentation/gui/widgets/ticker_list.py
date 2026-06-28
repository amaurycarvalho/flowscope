import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from PIL import Image, ImageTk

from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope.presentation.main import _resolve_icon_path


class TickerList:
    def __init__(self, parent: tk.Widget, on_change: callable = None, on_load: callable = None, initialdir: str = None, on_dir_changed: callable = None, on_index_click: dict[str, callable] = None):
        self.frame = tk.Frame(parent)
        self._on_change = on_change
        self._on_load = on_load
        self._initialdir = initialdir
        self._on_dir_changed = on_dir_changed

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
        self._text.bind("<Control-a>", self._on_select_all)
        self._text.bind("<Control-A>", self._on_select_all)

        self._icon_refs: list[ImageTk.PhotoImage] = []

        def _load_icon(filename: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
            path = _resolve_icon_path(filename)
            img = Image.open(path).resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._icon_refs.append(photo)
            return photo

        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        btn_load = tk.Button(
            btn_frame, image=_load_icon("document-open.png"),
            command=self._load, cursor="hand2", padx=0,
        )
        btn_load.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_load, "Carregar lista de tickers de arquivo")

        btn_save = tk.Button(
            btn_frame, image=_load_icon("document-save.png"),
            command=self._save, cursor="hand2", padx=0,
        )
        btn_save.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_save, "Salvar lista de tickers em arquivo")

        btn_filter = tk.Button(
            btn_frame, image=_load_icon("edit-find.png"),
            command=self._filter, cursor="hand2", padx=0,
        )
        btn_filter.pack(side=tk.LEFT, padx=2)
        ToolTip(btn_filter, "Filtrar tickers exibidos")

        if on_index_click:
            for label, callback in on_index_click.items():
                tk.Button(btn_frame, text=label, command=callback, cursor="hand2").pack(side=tk.LEFT, padx=2)

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

    def _on_select_all(self, event=None):
        self._select_all()
        return "break"

    def _clear_selection(self):
        self._text.tag_remove(tk.SEL, "1.0", tk.END)

    def _save(self) -> None:
        path = filedialog.asksaveasfilename(
            initialdir=self._initialdir,
            defaultextension=".txt",
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if path:
            Path(path).write_text("\n".join(self.get_tickers()), encoding="utf-8")
            if self._on_dir_changed:
                self._on_dir_changed(Path(path).parent)

    def _filter(self) -> None:
        if self._on_change:
            self._on_change()

    def _load(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=self._initialdir,
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if path and Path(path).exists():
            content = Path(path).read_text(encoding="utf-8")
            self._text.delete("1.0", tk.END)
            self._text.insert("1.0", content)
            if self._on_dir_changed:
                self._on_dir_changed(Path(path).parent)
            if self._on_load:
                self._on_load()
