## Why

Operações de refresh de painel (troca de aba, edição de tickers, seleção de ticker) e cópia de gráfico via toolbar do matplotlib executam síncrono na thread principal do tkinter, travando a interface por centenas de ms a segundos sem qualquer feedback visual de "processando". O cursor não muda para "watch" (hourglass), fazendo o usuário pensar que o programa travou.

## What Changes

- Refatorar `_enter_loading_state` / `_exit_loading_state` em duas camadas: uma camada base de cursor (genérica) e a camada pesada atual (cursor + desabilitar inputs + animação)
- Adicionar `_set_wait_cursor()` / `_clear_wait_cursor()` como métodos reutilizáveis de uso geral
- Envolver com try/finally os seguintes pontos com cursor watch:
  - `_on_tab_changed` — refresh de charts ao trocar de aba
  - `_on_ticker_edit` — refresh ao editar lista de tickers
  - `_on_ticker_combo_selected` — refresh ao selecionar ticker (delega para `_on_tab_changed`)
  - `_copy_chart` — cópia de imagem do gráfico (savefig + xclip)
- `_enter_loading_state` / `_exit_loading_state` passam a delegar o cursor para os novos métodos

## Capabilities

### New Capabilities

Nenhuma. Mudança puramente de implementação/UI — não altera requisitos funcionais do sistema.

### Modified Capabilities

Nenhuma. Comportamento visível ao usuário permanece idêntico, apenas com feedback visual adicional.

## Impact

- `src/flowscope/presentation/gui/app.py`: ~10 linhas novas (2 métodos) + alterações em 2 métodos existentes + try/finally em 4 call sites
- `src/flowscope/presentation/gui/charts/toolbar.py`: sem alterações (callback `_copy_chart` fica no app.py)
- `src/flowscope/infrastructure/clipboard_image.py`: sem alterações
- Nenhuma dependência nova, nenhuma API alterada
