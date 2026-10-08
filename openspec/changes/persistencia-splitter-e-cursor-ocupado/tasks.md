## 1. Persistência do divisor por largura

- [x] 1.1 Em `app.py::_on_close`, substituir a captura de `sash_coord` das duas PanedWindows pelo cálculo de `largura_direita` do divisor principal; verificar relendo `~/.flowscope/config.json` que a chave `sash_positions` passa a conter a largura numérica
- [x] 1.2 Remover/neutralizar a `_left_pw` de painel único em `app_layout.py`, adicionando `_main_notebook` diretamente ao `_main_pw`; verificar que a janela constrói e que `_main_pw.sash_coord(0)` não levanta `TclError`
- [x] 1.3 Implementar a restauração da largura após o primeiro `<Map>`/`<Configure>` com a janela no tamanho final e clamp que preserve o painel esquerdo em `app_layout.py`/`app_tab_layout.py::_restore_sashes`; verificar que, após reabrir, a largura do painel direito bate com a salva
- [x] 1.4 Descartar o formato legado de `sash_positions` (lista de posição) na leitura de preferências e aplicar o layout padrão; verificar com um `config.json` legado de 4 valores que o divisor usa o padrão e passa a gravar a largura
- [x] 1.5 Adicionar testes de save/restore do divisor (resolução maior e menor) e verificar com `make test`

## 2. Cursor de espera sem vazamentos

- [x] 2.1 Em `app_status.py::_on_busy_motion`, registrar o cursor de repouso do widget sob o ponteiro quando ainda não rastreado; verificar com teste que um widget criado após `_set_wait_cursor` volta ao repouso em `_clear_wait_cursor`
- [x] 2.2 Expor um acessor público de "ocupado" na autoridade única (`presenter.py`) e usar em `_on_busy_motion` para auto-limpar o `watch` e desinstalar o hook quando ocioso; verificar com teste que um `watch` residual é limpo no primeiro `<Motion>` sem operação ativa
- [x] 2.3 Substituir `unbind_all("<Motion>")` por remoção do binding específico do hook; verificar com teste que `exit_busy` repetido não remove outros bindings globais de `<Motion>`
- [x] 2.4 Confirmar que managers locais (chat e preview de documentos) não acionam o cursor global; verificar com teste que o cursor permanece inalterado durante esses jobs

## 3. Validação integrada

- [x] 3.1 Estender `tests/test_presentation/test_button_state.py` cobrindo os cenários novos de cursor e verificar com `make test`
- [x] 3.2 Rodar `make lint` e `make quality-gate` e corrigir eventuais regressões
- [x] 3.3 Validar manualmente (com display) que ajustar o divisor, fechar e reabrir em resolução diferente preserva a largura do painel direito e não deixa hourglass preso
