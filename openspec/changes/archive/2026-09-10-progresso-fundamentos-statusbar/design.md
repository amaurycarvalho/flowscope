## Context

Ver `proposal.md - Why`. O fluxo atual (`controller.on_load_data`) executa a carga histórica com um `ProgressReporter`, chama `on_result` (que renderiza os gráficos de forma síncrona), inicia a análise fundamentalista em uma thread (`FundamentalJob`) e drena a fila na thread do Tk (`_drenar_fundamental`). O progresso por ticker é publicado como `(MENSAGEM_PROGRESSO, detalhe, falhou)` e exibido por `on_fundamental_progress` via `set_status(detalhe, "ℹ")`, que esconde a barra (`pack_forget`). O cursor `watch` é definido na janela raiz, mas botões e lista de tickers definem `cursor="hand2"` individualmente, sobrepondo o cursor da janela.

## Goals / Non-Goals

**Goals:**
- Exibir a barra de progresso durante a fase de Fundamentos, com `current`/`total` e estado inicial `0/N`.
- Substituir o glifo `ℹ` por um marcador de renderização consistente.
- Aplicar o cursor `watch` a todos os widgets interativos, restaurando os cursores originais.

**Non-Goals:**
- Reduzir o tempo de renderização síncrona dos gráficos em `on_result` (pausa distinta, fora dos três pontos).
- Alterar o fluxo de progresso da carga histórica.
- Mudar contratos de domínio ou de aplicação.

## Decisions

### Progresso da fase fundamental via `set_progress`, não `set_status`

`on_fundamental_progress` passa a chamar `set_progress(current, total, label)`, que empacota a barra e atualiza o rótulo. O `set_status` atual esconde a barra (`pack_forget`) e não serve para progresso.

- **Alternativa descartada**: manter `set_status` e adicionar um ícone — a barra continuaria oculta.

### Mensagem do job carrega `current`/`total`

`FundamentalJob` mantém um contador de mensagens de progresso e publica `(MENSAGEM_PROGRESSO, detalhe, falhou, current, total)`, com `total = len(tickers)`. O caso de uso emite exatamente um evento por ticker (sucesso ou falha), então o contador é confiável.

- **Alternativa descartada**: mudar a assinatura do callback do caso de uso para incluir `current`/`total` — espalha mudança por aplicação/domínio e seus testes, sem ganho real.
- **Alternativa descartada**: extrair `(indice/total)` do texto do detalhe — frágil a mudanças de formato.

### Estado inicial `0/N` e limpeza condicional da barra

`_iniciar_analise_fundamental` emite um `on_progress(0, N, "• Fundamentos...")` ao iniciar o job, para a barra aparecer imediatamente. `on_operation_finished` passa a limpar a barra apenas quando `_operacoes_ativas == 0`, evitando que o `finally` da carga esconda a barra antes da fase fundamental.

- **Alternativa descartada**: deixar a limpeza incondicional e depender da primeira mensagem de ticker — deixaria um intervalo sem barra durante o primeiro ticker.

### Marcador de status `•` (U+2022)

Substituir `ℹ` (U+2139) por `•` (U+2022), que renderiza de forma universal. Os ícones de desfecho `✓` e `⚠` são mantidos.

- **Alternativa descartada**: `⏳`, `⟳` ou `→` — suporte irregular em fontes, contrariando o objetivo de consistência.

### Cursor `watch` em toda a árvore de widgets

`StatusMixin` percorre recursivamente a árvore de widgets, guarda o cursor atual de cada um, aplica `watch` e restaura ao final. Uma flag evita repercorrer enquanto a operação está ativa.

- **Alternativa descartada**: listar manualmente os widgets com cursor próprio — quebra a cada widget novo.
- **Alternativa descartada**: definir `watch` só na janela raiz — filhos com cursor próprio continuam sobrepondo.

### Controles permanecem desabilitados durante a fundamental

`on_operation_finished` restaura os controles apenas quando `_operacoes_ativas == 0`, e `on_fundamental_finished` também restaura nesse ponto. Como a fase fundamental incrementa o contador antes do `finally` da carga histórica, os controles permanecem desabilitados até a análise concluir. Para não corromper o snapshot de estados quando uma nova operação começa com os controles já desabilitados (ex.: F5/Enter durante a análise), `_disable_all_buttons` passa a ser idempotente: não sobrescreve um snapshot ativo.

- **Alternativa descartada**: desabilitar novamente em `on_fundamental_started` — sobrescreveria o snapshot com os estados já desabilitados e a restauração deixaria os controles desabilitados.

## Risks / Trade-offs

- **[Custo de percorrer a árvore de widgets]** → feito uma vez por operação (guardado por flag), não a cada atualização.
- **[Alguns widgets podem rejeitar `cursor`]** → `tk.TclError` capturado por widget.
- **[Mudança no formato da mensagem do job]** → o controller tolera mensagens sem `current`/`total`, tratando-as como progresso sem barra.
- **[Barra e rótulo compartilham a mesma variável]** → `set_progress` define o rótulo; as mensagens de desfecho via `set_status` sobrescrevem e escondem a barra, que é o estado final desejado.
- **[Pausa da renderização de gráficos permanece]** → documentada como não escopo.

## Migration Plan

Sem migração de dados; mudança de apresentação. Rollback = reverter a change.

## Open Questions

- Nenhuma. O marcador `•` é uma suposição registrada; se houver preferência por outro glifo, basta trocar a constante.
