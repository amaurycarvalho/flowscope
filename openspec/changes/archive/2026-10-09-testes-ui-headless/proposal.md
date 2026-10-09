## Why

A primeira onda (`reduzir-testes-ui`) tornou o orçamento de testes de UI verificável e baixou o teto de 250 para **225**. Restam, contudo, declarações gated que continuam exercitando **lógica que não depende de Tk** por falta de costura: os painéis matplotlib montam `Figure`/`Axes` (lógica pura) e o `FigureCanvasTkAgg` (única dependência real de Tk) no mesmo construtor; e mixins (`DocumentFlowMixin`, `StatusMixin`) derivam decisões (habilitar botão, estado de resumo, config aplicada) gravando diretamente em widgets, sem expor o resultado como valor testável. O teto não permite regressão, mas também não reduz sozinho o estoque remanescente.

## What Changes

- Extrai **costuras testáveis** na apresentação para que a lógica hoje presa ao widget seja verificável sem `DISPLAY`:
  - Painéis de gráfico passam a separar a construção do `Figure`/`Axes` (pura) do invólucro Tk (`Frame` + `FigureCanvasTkAgg` + toolbar), permitindo testar com `Figure()` puro.
  - Mixins passam a expor decisões como valores/funções puras (ex.: `resumir_habilitado() -> bool`, `abrir_habilitado() -> bool`) e os widgets apenas consomem o resultado.
  - Diálogo de configuração de LLM separa o modelo de formulário (carga, presets, provedor ativo) dos `StringVar` do Tk.
- Converte para headless as declarações gated correspondentes, preservando a asserção de comportamento observável (paridade de textos, números e ordem).
- Migra para `tests/test_application`/`tests/test_presentation` headless qualquer lógica pura hoje coberta sob gate de display.
- Baixa o baseline `tests/architecture/ui_test_budget.txt` após cada incremento (o ratchet exige atualização explícita).
- Mantém sob teste de UI apenas o que só existe com Tk: layout/geometria, eventos de ponteiro, `Treeview`/notebooks reais, `ReadonlyText`/clipboard, overlay/modal e o binding fio-a-fio do estado aos widgets.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `presentation-test-coverage`: o componente de apresentação cuja lógica não depende intrinsecamente de Tk DEVE expor costura que permita verificação headless (construção de figura separada do canvas; decisões derivadas expostas como valores), e o teste de UI DEVE ficar restrito ao widget.

## Impact

- `src/flowscope/presentation/gui/charts/fundamental_evolution_panel.py` e `correlation_network_panel.py`: separação figura/canvas (lógica pura por trás de uma costura).
- `src/flowscope/presentation/gui/charts/document_tree_panel.py` e `document_flow_mixin.py`: exposição de decisões (habilitação de "Resumir pendentes"/"Abrir documento") como valores puros.
- `src/flowscope/presentation/gui/llm/config_dialog.py`: extração do modelo de formulário de configuração.
- `tests/test_presentation/test_fundamental_evolution_panel.py`, `test_correlation_network_panel.py`, `test_document_tree_panel.py`, `test_noticias_panel.py`, `test_llm_config_dialog.py`, `test_button_state.py`: conversão para headless.
- `tests/architecture/ui_test_budget.txt`: baseline reduzido (parte de **225**).
- Delta em `openspec/specs/presentation-test-coverage/spec.md`.
- Sem mudança de comportamento do produto: paridade observável exigida (o spec `layer-boundaries` já requer paridade).
- Depende de `reduzir-testes-ui` (guardrail de teto com ratchet e baseline em arquivo), já arquivada.
