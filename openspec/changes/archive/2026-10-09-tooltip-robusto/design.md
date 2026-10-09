## Context

Ver `proposal.md` — Why. `presentation/gui/widgets/tooltip.py` é a única implementação de tooltip, usada pela barra superior, lista de tickers, painéis de Documentos/Notícias, chat, toolbar de gráficos e pelo seletor de modelo. O defeito está confinado à classe: `_enter` (`:22`) reagenda sobrescrevendo `_after_id` sem cancelar o pendente; `_show` (`:33`) cria e sobrescreve `_tip_window` sem destruir o existente; `_hide` (`:51`) destrói apenas o último. Reproduzido de forma determinística: duas exibições antes de um `<Leave>` deixam uma janela órfã sem referência.

## Goals / Non-Goals

**Goals:**
- Garantir no máximo uma janela e um agendamento vivos por instância de `ToolTip`.
- Cobrir o comportamento com testes unitários do widget.

**Non-Goals:**
- Alterar textos, atraso, posição ou aparência dos botões e dos tooltips já existentes.
- Investigar/reproduzir o gatilho exato de eventos no ambiente do usuário (a correção torna o sintoma impossível independentemente do gatilho).

## Decisions

### 1. Endurecer a classe única em vez de cada ponto de uso

Corrigir `ToolTip` centralmente beneficia todos os tooltips e evita duplicar defesas. Alternativa: tratar apenas o seletor de modelo. Rejeitada: o vazamento é da classe e pode atingir qualquer tooltip.

### 2. Invariantes explícitos

- `_enter`: se houver `_after_id`, cancelar antes de reagendar.
- `_show`: zerar `_after_id` e, se `_tip_window` existir, destruí-la antes de criar a nova.
- `_leave`/`_hide`: manter o cancelamento e a destruição, protegendo `after_cancel` com `try/except tk.TclError` para tolerar agendamentos já disparados.

### 3. Testes do ciclo de vida

Testes headless (sem `needs_display`) que usam um widget falso e substituem `tk.Toplevel`/`tk.Label`, disparando dois `<Enter>` sem `<Leave>` e verificando que resta uma única janela; que um `<Leave>` destrói a janela; que um clique destrói a janela; e que sair antes do atraso não exibe a dica. Alternativa: testes de widget com `needs_display`. Rejeitada: o comportamento é puro e a suíte tem um teto de testes de UI que só encolhe, então cobri-lo sem `DISPLAY` mantém o orçamento e é mais estável.

### 4. Cobertura de tooltips em todos os botões

Todos os botões da aplicação devem expor uma dica. A decisão é varrer os pontos de criação de `tk.Button`/`ttk.Button` e atribuir uma dica descritiva aos que ainda não tinham, reutilizando a `ToolTip` endurecida em vez de qualquer mecanismo paralelo. Alternativa: cobrir apenas os botões de ícone (sem texto visível). Rejeitada: botões com texto também se beneficiam de descrições mais completas, e a uniformidade evita pontos cegos. As dicas foram adicionadas em `app_layout` (botão de atalho no desktop e parada), `charts/noticias_panel` (Atualizar, Abrir, Resumir pendentes), `charts/document_tree_panel` (Atualizar, Abrir documento, Resumir pendentes), `chat/chat_panel` (Copiar chat, Limpar, Enviar, Cancelar), `llm/config_dialog` (Salvar, Cancelar, Testar) e `widgets/about_panel` (GitHub, log e release).

## Risks / Trade-offs

- **[Risco] `after_cancel` de id já disparado levantar `TclError` em algum Tk** → capturado no `_leave`.
- **[Trade-off] Reposicionar a janela em reexibição** → como a janela anterior é destruída, a nova é criada com a posição atual do widget, comportamento desejado.
