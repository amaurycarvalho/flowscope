## Context

Ver `proposal.md` — Why. `presentation/gui/widgets/tooltip.py` é a única implementação de tooltip, usada pela barra superior, lista de tickers, painéis de Documentos/Notícias, chat, toolbar de gráficos e pelo seletor de modelo. O defeito está confinado à classe: `_enter` (`:22`) reagenda sobrescrevendo `_after_id` sem cancelar o pendente; `_show` (`:33`) cria e sobrescreve `_tip_window` sem destruir o existente; `_hide` (`:51`) destrói apenas o último. Reproduzido de forma determinística: duas exibições antes de um `<Leave>` deixam uma janela órfã sem referência.

## Goals / Non-Goals

**Goals:**
- Garantir no máximo uma janela e um agendamento vivos por instância de `ToolTip`.
- Cobrir o comportamento com testes unitários do widget.

**Non-Goals:**
- Alterar textos, atraso, posição, aparência ou pontos de uso.
- Investigar/reproduzir o gatilho exato de eventos no ambiente do usuário (a correção torna o sintoma impossível independentemente do gatilho).

## Decisions

### 1. Endurecer a classe única em vez de cada ponto de uso

Corrigir `ToolTip` centralmente beneficia todos os tooltips e evita duplicar defesas. Alternativa: tratar apenas o seletor de modelo. Rejeitada: o vazamento é da classe e pode atingir qualquer tooltip.

### 2. Invariantes explícitos

- `_enter`: se houver `_after_id`, cancelar antes de reagendar.
- `_show`: zerar `_after_id` e, se `_tip_window` existir, destruí-la antes de criar a nova.
- `_leave`/`_hide`: manter o cancelamento e a destruição, protegendo `after_cancel` com `try/except tk.TclError` para tolerar agendamentos já disparados.

### 3. Testes do ciclo de vida

Testes de widget (marcados com `needs_display`, como os demais de apresentação) que disparam dois `<Enter>` sem `<Leave>` e verificam que resta uma única janela; que um `<Leave>` destrói a janela; e que sair antes do atraso não exibe a dica. Alternativa: teste de integração pela GUI. Rejeitada: o comportamento é da classe e o teste unitário é direto e estável.

## Risks / Trade-offs

- **[Risco] `after_cancel` de id já disparado levantar `TclError` em algum Tk** → capturado no `_leave`.
- **[Trade-off] Reposicionar a janela em reexibição** → como a janela anterior é destruída, a nova é criada com a posição atual do widget, comportamento desejado.
