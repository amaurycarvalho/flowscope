## 1. Correção do baseline do cursor

- [x] 1.1 Adicionar `StatusMixin._cursor_de_repouso(widget)` em `src/flowscope/presentation/gui/app_status.py`, normalizando tupla/lista devolvida por `cget("cursor")` para o nome do cursor e filtrando os cursores transitórios (`hresize`, `sb_h_double_arrow`, `sb_v_double_arrow`); verificar com teste de GUI que um cursor em forma de lista não é usado como baseline
- [x] 1.2 Usar `_cursor_de_repouso` no snapshot de `_set_wait_cursor` e no hook `_on_busy_motion`; verificar que o cursor `"watch"` continua sendo aplicado e restaurado normalmente
- [x] 1.3 Em `_clear_wait_cursor`, restaurar o baseline e, em caso de `TclError`, aplicar `cursor=""` como fallback, evitando que o widget permaneça em `"watch"`

## 2. Testes de regressão

- [x] 2.1 Adicionar teste de GUI em `tests/test_presentation/test_fundamental_table.py` (`TestFundamentalTableCursorSync`) com o ponteiro sobre o separador do grid rolável antes de iniciar a operação, verificando que o cursor não permanece `"watch"` ao final; confirmar que o teste falha sem a correção e passa com ela
- [x] 2.2 Confirmar que os testes existentes de sincronização dos dois grids e de cursores (`TestWaitCursor`, `TestWaitCursorFundamentos`, `TestFundamentalTableCursorSync`) continuam passando

## 3. Investigação do atraso percebido no sincronismo de seleção

- [x] 3.1 Medir com o painel real e o app completo o intervalo entre o clique e a seleção espelhada nos dois sentidos; confirmar que o espelhamento de estado ocorre de forma síncrona e imediata (`_espelhar_selecao`)
- [x] 3.2 Profilar (`cProfile`) o redesenho posterior ao clique e confirmar que não há tempo relevante em callbacks Python (todo o custo está no repaint C do Tk)
- [x] 3.3 Isolar a origem do custo ocultando `_frame_rolavel`/`_frame_fixo` e confirmar que o atraso é o repaint do grid de 28 colunas, idêntico nos dois sentidos; registrar a conclusão em `design.md` (nenhuma alteração de código)

## 4. Verificação final

- [x] 4.1 Rodar `ruff check src/` e `flake8 --max-complexity=10 --select=B,A,D --extend-exclude=tests ./src/` e confirmar que passam sem erros
- [x] 4.2 Rodar a suíte de testes da camada de apresentação (`pytest tests/test_presentation`) e confirmar que passa sem regressões
- [x] 4.3 Rodar `openspec validate "corrigir-vazamento-cursor-grid-fundamentos"` e confirmar que retorna `valid: true`
