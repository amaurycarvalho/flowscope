<!-- Ordenação: aplicar depois de `reduzir-testes-ui` (ou com folga prévia no
     baseline), pois o teste de UI do overlay adiciona 1 `@needs_display` e o
     ratchet daquela change reprova aumento sobre o baseline de 250. -->

## 1. Coordenador do gate e escudo

- [ ] 1.1 Criar o coordenador `StartupGate` (`iniciar()`/`finalizar()`) com flag `_inicializando`, recebendo a view (ou callbacks) e o presenter; verificar com teste headless que `iniciar` chama `enter`/coloca escudo e `finalizar` remove o escudo antes de `exit`
- [ ] 1.2 Implementar o escudo como `tk.Frame` transparente com `place(relwidth=1, relheight=1)` e `cursor="watch"`, com `lift()`, e verificar com teste de UI que o overlay aparece ao iniciar e some ao finalizar
- [ ] 1.3 Garantir idempotência do coordenador (chamadas repetidas de `iniciar`/`finalizar` não duplicam escudo nem desbalanceiam o contador) com teste headless

## 2. Integração com a inicialização

- [ ] 2.1 Chamar `iniciar_gate()` ao final de `FlowScopeGUI.__init__`, após `_wire_controller`, e verificar que o gate está ativo antes do `mainloop` (teste headless com view fake)
- [ ] 2.2 Chamar `finalizar_gate()` no fim de `_restore_tabs` (definido em `app_tab_layout.py`), após `_on_tab_changed`, dentro de `try/finally`, e verificar que o release ocorre após a restauração inicial
- [ ] 2.3 Cobrir os painéis sem `all_buttons()` (Chat AI/Sobre) garantindo que o escudo os bloqueia, e verificar que nenhum handler dispara durante a inicialização
- [ ] 2.4 Verificar que, quando `_on_tab_changed` da restauração submete um job de leitura (B/C) e o mesmo dispara `presenter.enter()`, o release do gate remove o escudo mas mantém controles/cursor ocupados até o job terminar (contador de operações), sem hourglass preso

## 3. Gate de atalhos

- [ ] 3.1 Guardar `_inicializando` no início dos handlers de `F5`, `Return` e `Ctrl+Shift+C` e verificar com teste headless que a ação é ignorada enquanto ativo
- [ ] 3.2 Verificar que, após o release, os atalhos voltam a funcionar normalmente

## 4. Liberação robusta

- [ ] 4.1 Adicionar `after` de segurança com timeout curto que força o release caso `_restore_tabs` não execute, e verificar com teste que a UI não fica presa
- [ ] 4.2 Verificar que uma falha na restauração inicial ainda remove o escudo, restaura controles/cursor e registra no log

## 5. Verificação final

- [ ] 5.1 Adicionar o delta de `loading-state-management` e validar o change
- [ ] 5.2 Rodar a suíte de apresentação, o guardrail de testes de UI, testes de complexidade e a checagem de fronteiras, confirmando que não há vazamento de hourglass e que a contagem de `@needs_display` não aumentou além do overlay (o overlay consome folga aberta por `reduzir-testes-ui`; sem folga, o guardrail reprova)
