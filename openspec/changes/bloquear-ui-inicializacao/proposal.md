## Why

Na versão compilada com PyInstaller, a janela é mapeada antes de o `mainloop` existir e a construção dos painéis (matplotlib, tabelas) roda de forma síncrona. Nesse intervalo o sistema operacional mantém o cursor de "aplicação iniciando" (hourglass), mas botões e abas já estão habilitados; cliques ficam enfileirados e, quando a fila é drenada junto com o trabalho pesado do primeiro `_on_tab_changed`, misturam transições de cursor e provocam o vazamento intermitente de hourglass/arrow. Falta um estado de inicialização que bloqueie a entrada até o Tk estar de fato disponível.

## What Changes

- Introduz um **gate de inicialização**: um escudo transparente cobrindo a janela (engole cliques em qualquer widget, inclusive abas e painéis sem `all_buttons()`), combinado com `disable_all_buttons()` para affordance e com o bloqueio dos atalhos globais (`F5`, `Return`, `Ctrl+Shift+C`) via flag de inicialização.
- O gate usa a autoridade única de estado ocupado (`FlowScopePresenter.enter/exit`) para travar controles e cursor de forma consistente, **dependendo** do `background-job-manager` (fatia A).
- O gate é liberado **após a restauração inicial de abas/painéis** (`_restore_tabs` → `_on_tab_changed` concluir), quando as leituras de catálogo já rodam em background por B/C.
- O release remove o escudo antes de restaurar o estado ocupado, para o snapshot de cursor não capturar o overlay.
- Testes do gate são headless (view fake), com apenas a existência/remoção do overlay em teste de UI, conforme `reduzir-testes-ui`.

## Capabilities

### New Capabilities
<!-- Nenhuma: o gate estende o estado ocupado e o ciclo de thread/queue já definidos. -->

### Modified Capabilities
- `loading-state-management`: adiciona o bloqueio de entrada durante a inicialização — estado ocupado, cursor e atalhos travados desde antes do `mainloop` até a restauração inicial de abas/painéis, com restauração consistente.

## Impact

- `src/flowscope/presentation/gui/app.py`: marcar o início do gate após o wiring e liberar no fim da restauração inicial.
- `src/flowscope/presentation/gui/app_layout.py`: `_restore_tabs` passa a sinalizar o término da restauração inicial ao gate.
- `src/flowscope/presentation/gui/app_status.py` / novo módulo de gate: escudo, flag `_inicializando` e gate dos atalhos (`_bind_shortcuts`/handlers).
- Delta em `openspec/specs/loading-state-management/spec.md`.
- Sem impacto em `domain`, `application` e `infrastructure`.
- **Dependências**: `background-job-manager` (autoridade de estado e lifecycle), `carga-principal-background` e `leituras-catalogo-background` (tornam o instante de "pronto" determinístico), `reduzir-testes-ui` (estratégia de teste headless e orçamento de UI).
