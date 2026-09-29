## Why

A carga principal (`on_load_data` e `on_index_clicked`) executa o download do portfólio e o processamento dos dados **de forma síncrona na thread do Tk**, bloqueando a janela por completo. É o último grande processamento não-UI preso ao event loop e a spec `process-cancellation` registra explicitamente essa dívida. Com o `BackgroundManager` da fatia A disponível, a carga principal pode migrar para o mesmo modelo assíncrono dos demais jobs, tornando-se cancelável e substituível.

## What Changes

- Migra `on_load_data`, `on_index_clicked` e a carga de portfólio de `on_ticker_edit` para o `BackgroundManager`, com política `latest_wins` no grupo `carga`.
- O download do portfólio e o processamento de indicadores passam a publicar progresso por evento; a renderização (`on_result`, `_iniciar_analise_fundamental`) permanece na thread do Tk via marshaling.
- **BREAKING (spec)**: a carga principal deixa de ser síncrona e não cancelável; o botão "interromper" passa a ficar visível durante ela.
- Uma nova requisição de carga principal **substitui** a anterior (supersede) e o job novo inicia com token limpo. Reentrada do **mesmo** acionamento continua bloqueada pelo `OperationGuard`, mantido como guarda de UI.
- Atualiza `process-cancellation`, `loading-state-management` e `presentation-test-coverage` para refletir o novo modelo.

## Capabilities

### New Capabilities
<!-- Nenhuma: a arquitetura de jobs é introduzida na fatia A sob `background-jobs`. -->

### Modified Capabilities
- `process-cancellation`: a carga principal passa a ser um processamento cancelável em background; o botão de interromper fica visível durante ela; a interrupção conjunta e o token reiniciado por operação passam a abranger a carga principal.
- `loading-state-management`: o estado ocupado, cursor e controles durante a carga principal passam a ser governados pelo ciclo de vida do job em background; a concorrência entre acionamentos passa a distinguir reentrada (ignorada) de nova operação (supersede).
- `presentation-test-coverage`: a cobertura do controller deixa de exigir o gerenciamento de fases do `ProgressReporter` na UI (migra para o worker) e passa a exigir a semântica de supersede/reentrada e testes headless, em vez de "segundo clique ignorado".

## Impact

- `src/flowscope/presentation/gui/controller_data.py`: `on_index_clicked`/`on_load_data` viram submissão de trabalho ao manager; `ProgressReporter` passa a ser alimentado por eventos do worker.
- `src/flowscope/presentation/gui/controller.py`: `on_ticker_edit` dispara a carga de portfólio via manager.
- `src/flowscope/presentation/gui/app_wiring.py`: wiring dos callbacks de ciclo de vida da carga.
- `presentation/gui/presenter.py`: contabilização do estado ocupado reage aos eventos do manager.
- Deltas em `openspec/specs/process-cancellation/spec.md` e `openspec/specs/loading-state-management/spec.md`.
- Sem impacto em `domain`, `application` e `infrastructure`. Depende da fatia A.
