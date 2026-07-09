import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from PIL import Image, ImageTk

from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope.presentation.main import _resolve_icon_path


class TickerList:
    def __init__(
        self, parent: tk.Widget,
        on_change: callable = None,
        on_load: callable = None,
        initialdir: str = None,
        on_dir_changed: callable = None,
        on_index_click: dict[str, callable] = None,
        on_data_needed: callable = None,
    ):
        self.frame = tk.Frame(parent)
        self._callbacks: dict[str, callable | dict] = {}
        self._callbacks["on_change"] = on_change
        self._callbacks["on_load"] = on_load
        self._callbacks["on_dir_changed"] = on_dir_changed
        self._callbacks["on_data_needed"] = on_data_needed
        self._callbacks["on_index_click"] = on_index_click or {}
        self._initialdir = initialdir
        self._view_mode = True
        self._icon_refs: list[ImageTk.PhotoImage] = []

        self._view_tickers_snapshot: list[str] = []
        self._view_selection_snapshot: set[str] = set()

        self._btn_frame = tk.Frame(self.frame)
        self._btn_frame.pack(fill=tk.X, pady=(0, 2))
        btn_frame = self._btn_frame

        self._btn_load = tk.Button(
            btn_frame, image=self._load_icon("document-open.png"),
            command=self._load, cursor="hand2", padx=0,
        )
        self._btn_load.pack(side=tk.LEFT, padx=2)
        ToolTip(self._btn_load, "Carregar lista de tickers de arquivo")

        self._btn_save = tk.Button(
            btn_frame, image=self._load_icon("document-save.png"),
            command=self._save, cursor="hand2", padx=0,
        )
        self._btn_save.pack(side=tk.LEFT, padx=2)
        ToolTip(self._btn_save, "Salvar lista de tickers em arquivo")

        sep1 = tk.Frame(btn_frame, width=2, relief=tk.RIDGE, bd=1)
        sep1.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        self._edit_toggle_var = tk.IntVar(value=0)
        self._edit_toggle = tk.Checkbutton(
            btn_frame, image=self._load_icon("document-properties.png"),
            variable=self._edit_toggle_var,
            command=self._on_mode_toggle, cursor="hand2", padx=0,
            indicatoron=0,
        )
        self._edit_toggle.pack(side=tk.LEFT, padx=2)
        ToolTip(self._edit_toggle, "Editar lista de tickers")

        self._btn_all = tk.Button(
            btn_frame, image=self._load_icon("edit-select-all.png"),
            command=self._select_all_listbox, cursor="hand2", padx=0,
        )
        self._btn_all.pack(side=tk.LEFT, padx=2)
        ToolTip(self._btn_all, "Selecionar Todos")

        self._btn_none = tk.Button(
            btn_frame, image=self._load_icon("edit-unselect-all.png"),
            command=self._deselect_all_listbox, cursor="hand2", padx=0,
        )
        self._btn_none.pack(side=tk.LEFT, padx=2)
        ToolTip(self._btn_none, "Desmarcar Todos")

        self._sep = tk.Frame(btn_frame, width=2, relief=tk.RIDGE, bd=1)
        self._sep.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        self._index_buttons: list[tk.Button] = []
        if on_index_click:
            for label in on_index_click:
                btn = tk.Button(
                    btn_frame, text=label,
                    command=lambda lb=label: self._callbacks.get("on_index_click", {}).get(lb, lambda: None)(),
                    cursor="hand2",
                )
                btn.pack(side=tk.LEFT, padx=2)
                self._index_buttons.append(btn)

        top_frame = tk.Frame(self.frame)
        top_frame.pack(fill=tk.X)
        tk.Label(top_frame, text="Tickers (um por linha):").pack(side=tk.LEFT, anchor=tk.W)
        self._counter_label = tk.Label(top_frame, text="", fg="gray")
        self._counter_label.pack(side=tk.RIGHT, padx=4)

        self._text_frame = tk.Frame(self.frame)
        self._text_frame.pack(fill=tk.BOTH, expand=True)

        self._text = tk.Text(self._text_frame, height=15, width=20)
        self._text_scrollbar = tk.Scrollbar(self._text_frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=self._text_scrollbar.set)
        self._text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = tk.Listbox(self._text_frame, selectmode=tk.EXTENDED, exportselection=False)
        self._listbox_scrollbar = tk.Scrollbar(self._text_frame, orient=tk.VERTICAL, command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=self._listbox_scrollbar.set)
        self._listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._text.bind("<Double-Button-1>", self._on_double_click)
        self._text.bind("<Button-3>", self._show_context_menu)
        self._text.bind("<Control-a>", self._on_select_all)
        self._text.bind("<Control-A>", self._on_select_all)
        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        self._context_menu = tk.Menu(self.frame, tearoff=0)
        self._context_menu.add_command(label="Copiar ticker", command=self._copy_selected_ticker)
        self._context_menu.add_command(label="Remover do filtro", command=self._remove_selected_ticker)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Selecionar todos", command=self._select_all)
        self._context_menu.add_command(label="Limpar seleção", command=self._clear_selection)

        self._set_view_mode(True)

    def _load_icon(self, filename: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
        path = _resolve_icon_path(filename)
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._icon_refs.append(photo)
        return photo

    def _set_view_mode(self, enable: bool) -> None:
        self._view_mode = enable
        if enable:
            self._text.pack_forget()
            self._text_scrollbar.pack_forget()
            self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self._listbox_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self._btn_all.pack(side=tk.LEFT, padx=2, before=self._sep)
            self._btn_none.pack(side=tk.LEFT, padx=2, before=self._sep)
            self._edit_toggle_var.set(0)
        else:
            self._listbox.pack_forget()
            self._listbox_scrollbar.pack_forget()
            self._btn_all.pack_forget()
            self._btn_none.pack_forget()
            self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self._text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self._edit_toggle_var.set(1)

    def _on_mode_toggle(self) -> None:
        edit_mode = bool(self._edit_toggle_var.get())
        if edit_mode:
            self._save_snapshot()
            self._set_view_mode(False)
        else:
            self._set_view_mode(True)
            self._restore_from_snapshot_edit()
            self._on_listbox_select()

    def _save_snapshot(self) -> None:
        self._view_tickers_snapshot = [self._listbox.get(i) for i in range(self._listbox.size())]
        self._view_selection_snapshot = {
            self._listbox.get(i) for i in self._listbox.curselection()
        }
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(self._view_tickers_snapshot))

    def _restore_from_snapshot_edit(self) -> None:
        text_tickers = self._get_text_tickers()
        old_set = set(self._view_tickers_snapshot)
        new_set = set(text_tickers)
        preserved = self._view_selection_snapshot & new_set
        added = new_set - old_set
        new_selection = preserved | added

        self._listbox.delete(0, tk.END)
        for t in text_tickers:
            self._listbox.insert(tk.END, t)
        for i, t in enumerate(text_tickers):
            if t in new_selection:
                self._listbox.selection_set(i)

        if new_set != old_set:
            self._view_tickers_snapshot = list(text_tickers)
            self._view_selection_snapshot = new_selection
            on_data_needed = self._callbacks.get("on_data_needed")
            if on_data_needed:
                on_data_needed()

    def _get_text_tickers(self) -> list[str]:
        content = self._text.get("1.0", tk.END).strip()
        return [t.strip().upper() for t in content.splitlines() if t.strip()]

    def set_counter(self, text: str) -> None:
        self._counter_label.config(text=text)

    def set_tickers(self, tickers: list[str]) -> None:
        self._listbox.delete(0, tk.END)
        for t in tickers:
            self._listbox.insert(tk.END, t)
        self._select_all_listbox()
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(tickers))
        self._view_tickers_snapshot = list(tickers)
        self._view_selection_snapshot = set(tickers)
        self._set_view_mode(True)

    def get_tickers(self) -> list[str]:
        if self._view_mode:
            return [self._listbox.get(i) for i in self._listbox.curselection()]
        return self._get_text_tickers()

    def get_all_listbox_tickers(self) -> list[str]:
        return [self._listbox.get(i) for i in range(self._listbox.size())]

    def _select_all_listbox(self) -> None:
        self._listbox.selection_set(0, tk.END)
        self._on_listbox_select()

    def _deselect_all_listbox(self) -> None:
        self._listbox.selection_clear(0, tk.END)

    def all_buttons(self) -> list[tk.Widget]:
        buttons = [
            self._btn_load, self._btn_save,
            self._edit_toggle, self._btn_all, self._btn_none,
        ]
        buttons.extend(self._index_buttons)
        return buttons

    def rebind(self, **callbacks) -> None:
        self._callbacks.update(callbacks)
        on_index_click = callbacks.get("on_index_click")
        if on_index_click is not None:
            for btn in self._index_buttons:
                btn.destroy()
            self._index_buttons.clear()
            for label in on_index_click:
                btn = tk.Button(
                    self._btn_frame, text=label,
                    command=lambda lb=label: self._callbacks.get("on_index_click", {}).get(lb, lambda: None)(),
                    cursor="hand2",
                )
                btn.pack(side=tk.LEFT, padx=2)
                self._index_buttons.append(btn)

    def _on_listbox_select(self, event=None) -> None:
        on_change = self._callbacks.get("on_change")
        if self._view_mode and on_change:
            on_change()

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
            on_dir_changed = self._callbacks.get("on_dir_changed")
            if on_dir_changed:
                on_dir_changed(Path(path).parent)

    def _filter(self) -> None:
        on_change = self._callbacks.get("on_change")
        if on_change:
            on_change()

    def _load(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=self._initialdir,
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if path and Path(path).exists():
            content = Path(path).read_text(encoding="utf-8")
            loaded = [
                t.strip().upper() for t in content.splitlines()
                if t.strip()
            ]
            self._listbox.delete(0, tk.END)
            for t in loaded:
                self._listbox.insert(tk.END, t)
            self._listbox.selection_set(0, tk.END)
            self._text.delete("1.0", tk.END)
            self._text.insert("1.0", "\n".join(loaded))
            self._view_tickers_snapshot = list(loaded)
            self._view_selection_snapshot = set(loaded)
            self._set_view_mode(True)
            on_dir_changed = self._callbacks.get("on_dir_changed")
            if on_dir_changed:
                on_dir_changed(Path(path).parent)
            on_load = self._callbacks.get("on_load")
            if on_load:
                on_load()
