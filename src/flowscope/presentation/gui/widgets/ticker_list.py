"""Widget de lista de tickers com modos de visualização e edição do FlowScope.

A classe ``TickerList`` alterna entre um modo de visualização baseado em
listbox e um modo de edição baseado em texto, com suporte a carregamento
e salvamento de arquivos e a botões de índice configuráveis pelo chamador.
"""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

from PIL import Image, ImageTk

from flowscope.presentation.gui.widgets.ticker_list_utils import (
    load_tickers,
    normalize_tickers,
    save_tickers,
)
from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope.presentation.main import _resolve_icon_path


class TickerList:
    """Lista de tickers com alternância entre modo de visualização e edição.

    No modo de visualização a listbox permite seleção múltipla, enquanto
    no modo de edição o campo de texto aceita um ticker por linha.
    """

    def __init__(
        self: "TickerList",
        parent: tk.Widget,
        on_change: Callable | None = None,
        on_load: Callable | None = None,
        initialdir: str | None = None,
        on_dir_changed: Callable | None = None,
        on_index_click: dict[str, Callable] | None = None,
        on_data_needed: Callable | None = None,
    ) -> None:
        """Inicializa a lista de tickers com seus botões e modos de exibição.

        Registra os callbacks recebidos e constrói a barra de ferramentas,
        a área de edição, o menu de contexto e os vínculos de eventos.
        """
        self.frame = tk.Frame(parent)
        self._callbacks: dict[str, Callable | dict] = {}
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

        self._build_toolbar(on_index_click)
        self._build_editor_area()
        self._build_context_menu()
        self._bind_events()

        self._set_view_mode(True)

    def _build_toolbar(self: "TickerList", on_index_click: dict | None) -> None:
        """Constrói a barra de botões de arquivo, edição e seleção.

        Empilha à esquerda os botões de carregar, salvar, alternar modo,
        selecionar todos, desmarcar todos e os botões de índice opcionais.
        """
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

        self._toolbar_separator()
        self._build_edit_toggle(btn_frame)

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

        self._sep = self._toolbar_separator()

        self._index_buttons: list[tk.Button] = []
        if on_index_click:
            for label in on_index_click:
                self._append_index_button(label)

    def _toolbar_separator(self: "TickerList") -> tk.Frame:
        """Adiciona um separador vertical à barra de ferramentas e o devolve.

        O separador é criado como um frame fino empilhado à esquerda da
        barra, servindo para agrupar visualmente os grupos de botões.
        """
        sep = tk.Frame(self._btn_frame, width=2, relief=tk.RIDGE, bd=1)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)
        return sep

    def _build_edit_toggle(self: "TickerList", btn_frame: tk.Frame) -> None:
        """Constrói o botão de alternância entre os modos de visualização e edição.

        Cria o checkbutton indicador que controla a troca entre a listbox
        e o campo de texto por meio da variável interna ``_edit_toggle_var``.
        """
        self._edit_toggle_var = tk.IntVar(value=0)
        self._edit_toggle = tk.Checkbutton(
            btn_frame, image=self._load_icon("document-properties.png"),
            variable=self._edit_toggle_var,
            command=self._on_mode_toggle, cursor="hand2", padx=0,
            indicatoron=0,
        )
        self._edit_toggle.pack(side=tk.LEFT, padx=2)
        ToolTip(self._edit_toggle, "Editar lista de tickers")

    def _append_index_button(self: "TickerList", label: str) -> None:
        """Adiciona um botão de índice que dispara o callback correspondente.

        O botão criado consulta o mapa ``on_index_click`` dos callbacks
        usando o rótulo capturado para acionar a ação correta.
        """
        btn = tk.Button(
            self._btn_frame, text=label,
            command=lambda lb=label: self._callbacks.get("on_index_click", {}).get(lb, lambda: None)(),
            cursor="hand2",
        )
        btn.pack(side=tk.LEFT, padx=2)
        self._index_buttons.append(btn)

    def _build_editor_area(self: "TickerList") -> None:
        """Constrói o cabeçalho, o campo de texto e a listbox da lista.

        Cria o rótulo de título, o contador, o campo de edição de texto e
        a listbox de visualização, cada um com sua barra de rolagem.
        """
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

    def _build_context_menu(self: "TickerList") -> None:
        """Constrói o menu de contexto exibido com o botão direito do mouse.

        O menu reúne ações de cópia, remoção, seleção total e limpeza da
        seleção aplicadas ao campo de texto do modo de edição.
        """
        self._context_menu = tk.Menu(self.frame, tearoff=0)
        self._context_menu.add_command(label="Copiar ticker", command=self._copy_selected_ticker)
        self._context_menu.add_command(label="Remover do filtro", command=self._remove_selected_ticker)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Selecionar todos", command=self._select_all)
        self._context_menu.add_command(label="Limpar seleção", command=self._clear_selection)

    def _bind_events(self: "TickerList") -> None:
        """Vincula os eventos de texto e de seleção da listbox.

        Registra os tratadores de clique duplo, menu de contexto, seleção
        total e mudança de seleção nos respectivos widgets.
        """
        self._text.bind("<Double-Button-1>", self._on_double_click)
        self._text.bind("<Button-3>", self._show_context_menu)
        self._text.bind("<Control-a>", self._on_select_all)
        self._text.bind("<Control-A>", self._on_select_all)
        self._listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

    def _load_icon(self: "TickerList", filename: str, size: tuple = (20, 20)) -> ImageTk.PhotoImage:
        """Carrega um ícone do recurso e o mantém referenciado para o Tk.

        A imagem é redimensionada para o tamanho informado e mantida na
        lista ``_icon_refs`` para evitar que o coletor de lixo a descarte.
        """
        path = _resolve_icon_path(filename)
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._icon_refs.append(photo)
        return photo

    def _set_view_mode(self: "TickerList", enable: bool) -> None:
        """Alterna entre o modo de visualização (listbox) e o de edição (text).

        Exibe apenas o widget correspondente ao modo ativo e sincroniza a
        variável do botão de alternância com o estado atual.
        """
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

    def _on_mode_toggle(self: "TickerList") -> None:
        """Lida com a alternância do modo de edição da lista de tickers.

        Ao entrar no modo de edição salva um retrato da listbox; ao sair,
        restaura a listbox a partir das edições e notifica a seleção.
        """
        edit_mode = bool(self._edit_toggle_var.get())
        if edit_mode:
            self._save_snapshot()
            self._set_view_mode(False)
        else:
            self._set_view_mode(True)
            self._restore_from_snapshot_edit()
            self._on_listbox_select()

    def _save_snapshot(self: "TickerList") -> None:
        """Salva o estado atual da listbox antes de entrar no modo de edição.

        Armazena a lista de tickers e a seleção corrente e preenche o
        campo de texto com o conteúdo para edição pelo usuário.
        """
        self._view_tickers_snapshot = [self._listbox.get(i) for i in range(self._listbox.size())]
        self._view_selection_snapshot = {
            self._listbox.get(i) for i in self._listbox.curselection()
        }
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(self._view_tickers_snapshot))

    def _restore_from_snapshot_edit(self: "TickerList") -> None:
        """Restaura a listbox a partir das edições feitas no modo de texto.

        Recalcula a seleção preservando os itens ainda presentes e somando
        os novos tickers, disparando ``on_data_needed`` se houver mudança.
        """
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

    def _get_text_tickers(self: "TickerList") -> list[str]:
        """Devolve a lista de tickers normalizada a partir do campo de texto.

        Lê todo o conteúdo do widget de texto e delega a normalização das
        linhas para a função auxiliar correspondente.
        """
        content = self._text.get("1.0", tk.END)
        return normalize_tickers(content)

    def set_counter(self: "TickerList", text: str) -> None:
        """Define o texto do contador exibido ao lado do cabeçalho."""
        self._counter_label.config(text=text)

    def set_tickers(self: "TickerList", tickers: list[str]) -> None:
        """Substitui a lista de tickers e atualiza a seleção no modo de visualização.

        Preenche a listbox e o campo de texto com os tickers recebidos,
        seleciona todos e atualiza os retratos de estado interno.
        """
        self._listbox.delete(0, tk.END)
        for t in tickers:
            self._listbox.insert(tk.END, t)
        self._select_all_listbox()
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(tickers))
        self._view_tickers_snapshot = list(tickers)
        self._view_selection_snapshot = set(tickers)
        self._set_view_mode(True)

    def get_tickers(self: "TickerList") -> list[str]:
        """Retorna os tickers selecionados ou editados conforme o modo atual.

        No modo de visualização devolve os itens selecionados na listbox;
        no modo de edição devolve as linhas digitadas no campo de texto.
        """
        if self._view_mode:
            return [self._listbox.get(i) for i in self._listbox.curselection()]
        return self._get_text_tickers()

    def get_all_listbox_tickers(self: "TickerList") -> list[str]:
        """Retorna todos os tickers presentes na listbox."""
        return [self._listbox.get(i) for i in range(self._listbox.size())]

    def _select_all_listbox(self: "TickerList") -> None:
        """Seleciona todos os itens da listbox e notifica a mudança."""
        self._listbox.selection_set(0, tk.END)
        self._on_listbox_select()

    def _deselect_all_listbox(self: "TickerList") -> None:
        """Remove a seleção de todos os itens da listbox."""
        self._listbox.selection_clear(0, tk.END)

    def all_buttons(self: "TickerList") -> list[tk.Widget]:
        """Retorna todos os botões do widget, incluindo os de índice."""
        buttons = [
            self._btn_load, self._btn_save,
            self._edit_toggle, self._btn_all, self._btn_none,
        ]
        buttons.extend(self._index_buttons)
        return buttons

    def rebind(self: "TickerList", **callbacks: object) -> None:
        """Atualiza os callbacks e recria os botões de índice se necessário.

        Mescla os novos callbacks com os existentes e, quando um novo mapa
        de índices é informado, reconstrói os botões correspondentes.
        """
        self._callbacks.update(callbacks)
        on_index_click = callbacks.get("on_index_click")
        if on_index_click is not None:
            self._rebuild_index_buttons(on_index_click)

    def _rebuild_index_buttons(self: "TickerList", on_index_click: dict) -> None:
        """Remove e recria os botões de índice com os novos rótulos."""
        for btn in self._index_buttons:
            btn.destroy()
        self._index_buttons.clear()
        for label in on_index_click:
            self._append_index_button(label)

    def _on_listbox_select(self: "TickerList", event: tk.Event | None = None) -> None:
        """Notifica a mudança de seleção quando o modo de visualização está ativo."""
        on_change = self._callbacks.get("on_change")
        if self._view_mode and on_change:
            on_change()

    def _on_double_click(self: "TickerList", event: tk.Event) -> None:
        """Filtra a lista com o ticker clicado duas vezes no modo de edição.

        Localiza a linha sob o cursor, reduz o texto a ela e notifica a
        mudança para que o filtro seja reaplicado.
        """
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

    def _show_context_menu(self: "TickerList", event: tk.Event) -> None:
        """Exibe o menu de contexto na posição do clique."""
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _copy_selected_ticker(self: "TickerList") -> None:
        """Copia o ticker selecionado ou a palavra sob o cursor para a área de transferência.

        Se houver uma seleção ativa copia o trecho selecionado; caso
        contrário copia a palavra sob a posição atual do cursor.
        """
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

    def _remove_selected_ticker(self: "TickerList") -> None:
        """Remove o ticker selecionado e refaz o filtro."""
        try:
            sel = self._text.tag_ranges(tk.SEL)
            if sel:
                self._text.delete(sel[0], sel[1])
                self._filter()
        except tk.TclError:
            pass

    def _select_all(self: "TickerList") -> None:
        """Seleciona todo o conteúdo do campo de texto."""
        self._text.tag_add(tk.SEL, "1.0", tk.END)

    def _on_select_all(self: "TickerList", event: tk.Event | None = None) -> str:
        """Seleciona todo o texto e interrompe o tratamento do evento padrão."""
        self._select_all()
        return "break"

    def _clear_selection(self: "TickerList") -> None:
        """Limpa a seleção atual do campo de texto."""
        self._text.tag_remove(tk.SEL, "1.0", tk.END)

    def _save(self: "TickerList") -> None:
        """Salva os tickers atuais em um arquivo escolhido pelo usuário.

        Abre a caixa de diálogo de salvamento e, ao escolher um caminho,
        grava os tickers do modo atual e notifica a mudança de diretório.
        """
        path = filedialog.asksaveasfilename(
            initialdir=self._initialdir,
            defaultextension=".txt",
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        save_tickers(Path(path), self.get_tickers())
        on_dir_changed = self._callbacks.get("on_dir_changed")
        if on_dir_changed:
            on_dir_changed(Path(path).parent)

    def _filter(self: "TickerList") -> None:
        """Notifica o callback de mudança para aplicar o filtro atual."""
        on_change = self._callbacks.get("on_change")
        if on_change:
            on_change()

    def _load(self: "TickerList") -> None:
        """Carrega tickers de um arquivo escolhido pelo usuário.

        Abre a caixa de diálogo de abertura, lê e normaliza os tickers do
        arquivo e notifica os callbacks de diretório e de carregamento.
        """
        path = filedialog.askopenfilename(
            initialdir=self._initialdir,
            filetypes=[("Arquivo de tickers", "*.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        if not Path(path).exists():
            return
        self._apply_loaded_tickers(load_tickers(Path(path)))
        on_dir_changed = self._callbacks.get("on_dir_changed")
        if on_dir_changed:
            on_dir_changed(Path(path).parent)
        on_load = self._callbacks.get("on_load")
        if on_load:
            on_load()

    def _apply_loaded_tickers(self: "TickerList", loaded: list[str]) -> None:
        """Popula a lista e o texto com os tickers carregados do arquivo.

        Substitui o conteúdo da listbox e do campo de texto, seleciona os
        itens e atualiza os retratos de estado antes de voltar à exibição.
        """
        self._listbox.delete(0, tk.END)
        for t in loaded:
            self._listbox.insert(tk.END, t)
        self._listbox.selection_set(0, tk.END)
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", "\n".join(loaded))
        self._view_tickers_snapshot = list(loaded)
        self._view_selection_snapshot = set(loaded)
        self._set_view_mode(True)
