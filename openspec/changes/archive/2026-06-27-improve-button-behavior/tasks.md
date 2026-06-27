## 1. Dados carregados ao clicar em "Hoje"

- [x] 1.1 Modificar `_on_today()` em `app.py` para chamar `self._on_load_data()` após `set_date(date.today())`
- [x] 1.2 Desabilitar botão "Hoje" durante carregamento em `_enter_loading_state()` e reabilitar em `_exit_loading_state()`; também desabilitar botão "Hoje" quando "Carregar" for clicado (mesmos métodos)

## 2. Persistência do último diretório nos diálogos de ticker

- [x] 2.1 Adicionar `last_ticker_dir` ao `DEFAULT_CONFIG` em `app.py`
- [x] 2.2 Adicionar parâmetros `initialdir` e `on_dir_changed` a `TickerList.__init__()` em `ticker_list.py`
- [x] 2.3 Modificar `TickerList._save()` para usar `self._initialdir` e invocar `on_dir_changed(path.parent)` após salvar
- [x] 2.4 Modificar `TickerList._load()` para usar `self._initialdir` e invocar `on_dir_changed(path.parent)` após carregar
- [x] 2.5 Atualizar a instanciação de `TickerList` em `FlowScopeGUI.__init__()` passando `initialdir=self._prefs.get("last_ticker_dir")` e `on_dir_changed=self._on_ticker_dir_changed`
- [x] 2.6 Criar método `_on_ticker_dir_changed(self, directory)` que atualiza `self._prefs["last_ticker_dir"]` em memória E persiste ao disco com `save_preferences(self._prefs)`
