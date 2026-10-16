## 1. Widget TickerList (sinais)

- [x] 1.1 Adicionar o callback `on_file_changed(path)` e acioná-lo em `_load` e `_save` com o caminho completo; verificar com teste em `tests/test_presentation/test_ticker_list.py` que ambos disparam com o path
- [x] 1.2 Adicionar o callback `on_content_changed` no ponto de detecção de mudança de conteúdo (`_restore_from_snapshot_edit`, quando `new_set != old_set`); verificar com teste que editar conteúdo dispara e que seleção/filtro não dispara

## 2. Estado e título na aplicação

- [x] 2.1 Adicionar `last_ticker_file` ao `DEFAULT_CONFIG` de `app.py` e lê-lo no startup; verificar em `tests/test_presentation/test_preferences.py` que a ausência da chave retorna `None`
- [x] 2.2 Implementar `_update_window_title()` compondo `TITLE_PREFIX + " — " + (basename | _index_name | "Nova lista.txt") + ("*" se dirty)`; verificar com teste que os formatos esperados são gerados
- [x] 2.3 Ligar os callbacks em `app_wiring.py`/`app_layout.py`: `on_file_changed` (guardar path + atualizar título + limpar dirty), `on_content_changed` (marcar dirty + atualizar título) e o clique de índice (definir `<ÍNDICE>.txt`, sem persistir/dirty); verificar com teste de integração
- [x] 2.4 Garantir que `last_ticker_file` é gravado no fechamento (`_on_close`) e no load/save; verificar com teste de round-trip

## 3. Testes

- [x] 3.1 Adicionar testes de composição do título: com arquivo, sem arquivo (`Nova lista.txt`), com asterisco após editar, sem asterisco por seleção e após índice (`IBOV.txt`)
- [x] 3.2 Adicionar testes de persistência da nova chave (gravação no load/save, não alteração no índice, restauração do nome no startup)
- [x] 3.3 Rodar os testes relacionados/impactados (`tests/test_presentation/test_ticker_list.py`, `test_preferences.py`, `test_controller.py` e afins) e garantir que passam

## 4. Verificação da change

- [x] 4.1 Rodar `make lint` e garantir ausência de erros
- [x] 4.2 Rodar `make complexity` e garantir ausência de regressões
- [x] 4.3 (manual, usuário) Rodar `make test`/`make quality-gate` apenas se considerar necessário por precaução
