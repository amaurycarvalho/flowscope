## Context

Ver `proposal.md - Why`. `FlowScopeGUI.__init__` (`app.py:97`) cria o root, constrói todos os painéis em `_build_main_area` (`app_layout.py:126`, incluindo os painéis matplotlib e a tabela de fundamentos) e só então chama `_wire_controller`, que cria o `FlowScopePresenter`. Em `_build_main_area` já é agendado `after(10, _restore_tabs)`, executado depois que o `mainloop` inicia. Nada chama `enter_busy`/`_disable_all_buttons` na inicialização; o hourglass observado é o cursor de "aplicação iniciando" do sistema operacional, e a janela mapeada aceita cliques que ficam enfileirados até o event loop drená-los junto com o primeiro `_on_tab_changed`.

Restrições:
- A autoridade única de estado ocupado é o `FlowScopePresenter` (`presenter.py`), com `enter/exit`, `disable_all_buttons`, `enter_busy`/`exit_busy` e contador de operações — introduzido/reforçado pela fatia A.
- `_disable_all_buttons` (`app_status.py:178`) não cobre abas de notebook, o `ChatPanel` nem o `AboutPanel`.
- Desabilitar abas via `notebook.tab(state=...)` depende do patchlevel do Tk empacotado; não é confiável.
- `_bind_shortcuts` (`app_layout.py:241`) usa `bind_all`, que dispara independentemente do foco.

## Goals / Non-Goals

**Goals:**
- Eliminar o vazamento de hourglass/arrow bloqueando toda a entrada até o Tk estar disponível.
- Cobertura completa (abas, chat, sobre, atalhos) sem depender de suporte do toolkit.
- Reutilizar a autoridade única de estado (A) e manter o gate testável headless (D).

**Non-Goals:**
- Reduzir o tempo de inicialização (apenas proteger o intervalo).
- Introduzir splash screen ou redesenhar a ordem de construção dos widgets.
- Alterar o comportamento de carregamento de dados (fatias B/C).

## Decisions

### Decisão 1: Escudo sobre a janela como mecanismo primário

**Escolha**: um `tk.Frame` sem conteúdo, com `place(x=0, y=0, relwidth=1, relheight=1)` e `cursor="watch"`, cobrindo o toplevel durante a inicialização; removido no release.

**Alternativas**: desabilitar widget a widget e prender abas revertendo a seleção em `_on_tab_changed`.

**Razão**: intercepta cliques em qualquer widget, inclusive abas e painéis sem `all_buttons()`, e não depende de `notebook.tab(state=...)`. Evita o flicker de reverter a seleção de aba.

### Decisão 2: O gate usa a autoridade única de estado

**Escolha**: `iniciar_gate()` chama `presenter.on_operation_started()` (que desabilita botões e aplica o cursor de espera) e coloca o escudo; `finalizar_gate()` remove o escudo e chama `presenter.on_operation_finished()`.

**Alternativas**: gerenciar cursor/controles diretamente no `FlowScopeGUI`, fora do presenter.

**Razão**: mantém a regra de operações concorrentes (o gate é uma operação como outra qualquer) e a restauração de baseline; uma operação em background iniciada durante a inicialização é contabilizada corretamente.

### Decisão 3: Gate dos atalhos por flag, mesmo com escudo

**Escolha**: um flag `_inicializando` guardado no início dos handlers de `F5`/`Return`/`Ctrl+Shift+C`; as bindings permanecem, mas as ações são ignoradas enquanto ativo.

**Alternativas**: (des)vincular os atalhos no início/fim do gate.

**Razão**: `bind_all` não respeita o escudo (não há foco capturado), então o escudo sozinho não cobre teclado. O flag é simples e não corre o risco de perder bindings por erro de pareamento.

### Decisão 4: Coordenador `StartupGate` e ponto de liberação

**Escolha**: extrair um coordenador enxuto (`iniciar()`/`finalizar()`) que concentra escudo, flag e chamadas ao presenter. `_restore_tabs` (`app_layout.py:241`) chama `finalizar()` ao final, depois de `_on_tab_changed()`, dentro de um `try/finally` para liberar mesmo em falha; o release agenda a remoção do escudo e só então a restauração do estado.

**Alternativas**: liberar no primeiro `after_idle` após o `mainloop`; liberar do próprio `app.py`.

**Razão**: a decisão tomada é liberar após a restauração inicial de abas/painéis; centralizar em `_restore_tabs` cobre o primeiro desenho e mantém `app.py` enxuto. O `finally` garante que um `TclError` não deixe a UI bloqueada.

### Decisão 5: Ordem do release

**Escolha**: remover o escudo **antes** de `presenter.on_operation_finished()`, para que o snapshot de baseline do cursor não inclua o overlay.

**Razão**: evita que a restauração capture/restaure o cursor do escudo e deixe resíduo.

### Decisão 6: Teste headless do gate

**Escolha**: `StartupGate` recebe uma view (ou callbacks) e é testado headless, com uma view fake que registra `colocar_escudo`/`remover_escudo`/`enter`/`exit` e o estado do flag. Apenas a existência e remoção do overlay no toplevel é teste de UI (uma unidade), conforme o orçamento de `layer-boundaries` e a estratégia de D.

**Razão**: a lógica (quando bloquear/liberar, ordem, `try/finally`) é verificável sem display; só o widget em si exige Tk.

## Risks / Trade-offs

- **[Risco]** Escudo com `place` sobre o toplevel pode não cobrir widgets em `place`/`pack` de toplevels auxiliares → **Mitigação**: colocar o escudo no próprio toplevel principal com dimensões relativas; opcionalmente `lift()`.
- **[Risco]** Um clique enfileirado ser drenado logo após o release e acionar uma aba → **Mitigação**: liberar somente quando a fila relevante já tiver sido processada (logo após `_restore_tabs`); o intervalo é mínimo e os testes cobrem o comportamento.
- **[Risco]** `_restore_tabs` não ser executado (ex.: `after` cancelado) e o gate nunca liberar → **Mitigação**: `finally` e, como rede, um `after` de segurança com timeout curto que força o release.
- **[Risco]** `enter_busy` custar a varredura de widgets no startup → **Trade-off** aceito; já é usado em toda operação.
- **[Trade-off]** Um overlay a mais na árvore de widgets → **Benefício**: cobertura total de entrada sem depender do toolkit.

## Migration Plan

1. Criar o coordenador `StartupGate` e o escudo, com teste headless da lógica e um teste de UI da presença/remoção do overlay.
2. Marcar `_inicializando` e chamar `iniciar_gate()` ao final de `FlowScopeGUI.__init__`, após `_wire_controller`.
3. Chamar `finalizar_gate()` no fim de `_restore_tabs` (em `try/finally`), após `_on_tab_changed`.
4. Gate dos atalhos nos handlers de `F5`/`Return`/`Ctrl+Shift+C`.
5. Adicionar o delta de `loading-state-management` e validar; rodar a suíte de apresentação, o guardrail de testes de UI e a checagem de fronteiras. Rollback = reverter o commit (sem migração de dados).
