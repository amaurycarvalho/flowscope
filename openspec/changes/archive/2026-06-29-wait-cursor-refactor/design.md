## Context

A classe `FlowScopeGUI` (`app.py:65`) gerencia o estado de carregamento com dois métodos:

- `_enter_loading_state()` (L438): desabilita inputs, seta `cursor="watch"`, `update_idletasks()`, inicia animação "Carregando..."
- `_exit_loading_state()` (L449): reabilita inputs, restaura cursor `""`, para animação

Este padrão é usado **apenas** em `_on_load_data()` (L483). Outras operações síncronas que bloqueiam a UI — refresh de charts via `_update_charts()`, cópia de gráfico via `_copy_chart()` — não têm qualquer feedback de cursor.

O problema é que `_enter/exit_loading_state` acoplam **três preocupações distintas**: cursor, desabilitação de inputs, e animação. Para operações leves (chart refresh ~500ms-2s, copy chart ~500ms-1s), desabilitar inputs e mostrar "Carregando..." na status bar é exagerado e semanticamente incorreto.

## Goals / Non-Goals

**Goals:**
- Separar o controle de cursor em métodos independentes e reutilizáveis
- Adicionar cursor watch em todas as operações síncronas que bloqueiam a UI
- Garantir que o cursor sempre retorne ao normal (via try/finally em todos os pontos)
- Manter `_enter/exit_loading_state` funcionando exatamente como hoje, apenas delegando o cursor

**Non-Goals:**
- Não alterar comportamento da animação "Carregando..."
- Não adicionar threading ou async (as operações permanecem síncronas)
- Não alterar a toolbar do matplotlib ou o mecanismo de cópia
- Não adicionar barra de progresso ou cancelamento

## Decisions

### 1. Arquitetura em 2 camadas

```
┌──────────────────────────────────────────────┐
│  _enter_loading_state()                      │
│  _exit_loading_state()                       │
│  (desabilita inputs + animação + DELEGA      │
│   → _set/_clear_wait_cursor)                 │
├──────────────────────────────────────────────┤
│  _set_wait_cursor()                          │
│  _clear_wait_cursor()                        │
│  (só cursor + update_idletasks)              │
└──────────────────────────────────────────────┘
```

**Rationale**: Desacoplar o cursor mecânico (sempre necessário) do estado pesado de loading (inputs desabilitados + animação). As operações leves usam só a camada de cima.

### 2. `update_idletasks()` obrigatório no set

`self.config(cursor="watch")` por si só não tem efeito visual imediato — o tkinter só processa a mudança no próximo ciclo de eventos. O `update_idletasks()` força o flush das tarefas de UI pendentes (incluindo mudança de cursor) **antes** da operação bloqueante começar.

### 3. try/finally em vez de context manager

Python `contextmanager` exigiria um gerador ou classe separada. O padrão try/finally é explícito, consistente com o estilo do código existente (já há try/except em `_on_load_data` e `_copy_chart`), e não adiciona abstração.

### 4. `_on_ticker_combo_selected` não recebe try/finally próprio

Porque ele delega para `_on_tab_changed()`, que já terá o cursor wrapping. Adicionar no combo seria redundante.

### 5. Sem specs de capacidade

Esta mudança é puramente de implementação/UX. Não altera requisitos funcionais — não há novas capabilities nem mudanças em specs existentes.

## Risks / Trade-offs

- **[Re-entrância]** Se o usuário clicar "Copiar Gráfico" repetidamente, o cursor vai piscar (watch → normal → watch). O finally garante que nunca fique travado em watch. Risco: baixo.
- **[Early return esquecido]** `_on_tab_changed` tem múltiplos early returns (L604-605, exceção; L607, `_charts_dirty` false). O wrapping com try/finally precisa cobrir **apenas** o bloco `if self._charts_dirty and self._current_data`, não o método inteiro. Risco: médio — requer atenção na implementação.
- **[Inicialização]** `_on_tab_changed` é chamado na inicialização via `_restore_tabs` (L402). Nesse ponto `_current_data` é `{}`, então o bloco não é executado. Mas se futuro caching popular `_current_data` no startup, o cursor precisaria funcionar corretamente já nesse momento.
- **[Consistência]** `_exit_loading_state` usa `cursor=""` (string) enquanto o padrão geral tkinter é usar string para cursor names. `_clear_wait_cursor` deve manter o mesmo padrão para consistência.
