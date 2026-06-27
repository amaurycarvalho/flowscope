## 1. Reposicionar barra de status

- [x] 1.1 Trocar ordem de chamada em `app.py.__init__`: `_build_statusbar()` antes de `_build_action_buttons()`

## 2. Adicionar botão "Filtrar"

- [x] 2.1 Adicionar `tk.Button(btn_frame, text="Filtrar", command=self._filter)` em `ticker_list.py`
- [x] 2.2 Criar método `_filter()` que chama `self._on_change()`
- [x] 2.3 Atualizar `_on_ticker_edit()` em `app.py` para exibir "Filtro aplicado!" na barra de status

## 3. Remover filtro automático

- [x] 3.1 Remover `self._text.bind("<KeyRelease>", self._on_key_release)` e o método `_on_key_release()` em `ticker_list.py`
- [x] 3.2 Remover `if self._on_change: self._on_change()` de `_load()` em `ticker_list.py`

## 4. Verificar

- [x] 4.1 Executar `pytest` e confirmar 46 testes passando
