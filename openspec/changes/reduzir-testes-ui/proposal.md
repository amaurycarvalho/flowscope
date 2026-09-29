## Why

A suíte de apresentação tem ~253 testes decorados com `@needs_display`, muitos cobrindo processamento ou lógica pura que não dependem de Tk. O spec `layer-boundaries` define um orçamento de testes de UI (wiring, estado de widget, empty-state e ciclo de thread/queue), mas nada o verifica automaticamente, e os testes estão fisicamente misturados nos módulos de UI (ex.: `TestPreview` de `flowscope.application.document_preview` em `test_document_tree_panel.py`). As fatias A/B/C param de adicionar processamento à UI, mas não reduzem o estoque existente. Esta change reduz a contagem de testes de UI ao mínimo estritamente necessário e trava um teto que só diminui.

## What Changes

- Migra testes de lógica pura de `tests/test_presentation` para `tests/test_application`/`tests/test_domain`, eliminando o gate `@needs_display` desnecessário.
- Converte para headless, via fakes de mixin/manager, os testes de UI que só exercitavam processamento (preview em thread, cache de texto, lote, geração de resumo).
- Consolida testes de estado de widget duplicados, mantendo um representante por comportamento observável.
- Introduz um **teto enforced** para os testes de UI: um baseline commitado da contagem de `@needs_display`, verificado por teste arquitetural que reprova aumento e exige queda — mesmo padrão da allowlist de fronteiras.
- Reconcilia `presentation-test-coverage` com o comportamento pós-A/B/C, exigindo verificação headless do processamento.

## Capabilities

### New Capabilities
<!-- Nenhuma: usa os specs existentes de orçamento de UI e cobertura de apresentação. -->

### Modified Capabilities
- `layer-boundaries`: o orçamento de testes de UI passa a ter verificação automatizada, com baseline que só encolhe.
- `presentation-test-coverage`: o processamento dos fluxos de apresentação DEVE ser verificado headless, com UI restrita ao comportamento que só existe com Tk.

## Impact

- Reorganização de `tests/test_presentation/**` (migração para `tests/test_application`/`tests/test_domain` e conversão para headless).
- Novo baseline `tests/architecture/ui_test_budget.txt` e verificação no guardrail arquitetural.
- Deltas em `openspec/specs/layer-boundaries/spec.md` e `openspec/specs/presentation-test-coverage/spec.md`.
- Sem impacto em `src/`. Depende das fatias A, B e C (a estrutura de jobs/leituras precisa estar estável).
