## 1. Top Bar — Substituir textos por ícones

- [x] 1.1 Adicionar imports de `PIL.Image` e `PIL.ImageTk` em `app.py`
- [x] 1.2 Criar helper `_load_icon` para carregar PNG via Pillow e redimensionar para 20×20
- [x] 1.3 Carregar ícones `document-open-recent.png`, `view-refresh.png` e `edit-copy.png` como atributos de instância
- [x] 1.4 Trocar `text=` por `image=` nos botões Hoje, Carregar e Copiar Dados, ajustando `padx`/`pady`

## 2. Sidebar — Substituir textos por ícones e unificar layout

- [x] 2.1 Adicionar imports de `PIL.Image`, `PIL.ImageTk` e `_resolve_icon_path` em `ticker_list.py`
- [x] 2.2 Carregar ícones `document-save.png`, `document-open.png` e `edit-find.png` como atributos de instância
- [x] 2.3 Trocar `text=` por `image=` nos botões Salvar Tickers, Carregar Tickers e Filtrar
- [x] 2.4 Adicionar `ToolTip` aos três botões da sidebar
- [x] 2.5 Fundir `btn_frame` e `btn_frame2` em um único frame horizontal: [save] [open] [filter] [IBOV] [IDIV] [IFIX] todos com `side=tk.LEFT`
- [x] 2.6 Remover `btn_frame2` e seu `pack` separado

## 3. Verificação

- [x] 3.1 Executar a aplicação em modo GUI e confirmar que todos os botões exibem ícones corretamente
- [x] 3.2 Verificar tooltips de todos os botões
- [x] 3.3 Verificar que IBOV/IDIV/IFIX estão na mesma linha dos botões de ação
- [x] 3.4 Confirmar que `_enter_loading_state`/`_exit_loading_state` continuam funcionando (referenciam `_load_button` e `_today_button` pelo nome do atributo, não pelo texto)
