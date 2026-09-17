## Context

Ver `proposal.md` para motivação. Hoje o ticker da "Análise do Ticker" é derivado por dois caminhos independentes:

- `_get_selected_ticker()` lê a seleção da TickerList e alimenta os gráficos de Dominância, Amplitude e Fluxo e o CSV da aba.
- `_evolution_ticker` é fixado por duplo-clique na tabela de Fundamentos e alimenta Evolução dos Fundamentos e Documentos (com fallback para `_get_selected_ticker()`).

A tabela de Fundamentos (`FundamentalTablePanel`) já tem seleção única (`selectmode="browse"`) espelhada entre dois `Treeview` (fixo/rolável), mas o evento `<<TreeviewSelect>>` só espelha a seleção; não há callback para a aplicação. O método `update()` apaga e reinsere todas as linhas, perdendo a seleção. As abas são construídas em `_build_ticker_tabs` iterando `TAB_CONFIGS` e marcando `state="disabled"` para nomes fora de `ENABLED_TABS`. A ordem da "Análise Geral" é hardcoded em `_build_general_tabs`.

## Goals / Non-Goals

**Goals:**
- Fonte única do ticker analisado: a linha selecionada na tabela de Fundamentos.
- Ordem de sub-abas e visibilidade conforme `proposal.md`.
- Preservar a seleção através de recargas da tabela e auto-selecionar a primeira linha.

**Non-Goals:**
- Implementar os painéis de Participação, Eficiência ou Diagnóstico (changes dedicadas).
- Alterar quais tickers compõem a tabela de Fundamentos (a TickerList continua filtrando as linhas).
- Persistir a seleção entre execuções da aplicação.

## Decisions

### 1. Estado da seleção vive na GUI, alimentado por callback da tabela
`FundamentalTablePanel` ganha um parâmetro `on_ticker_selected` invocado no `<<TreeviewSelect>>` com o ticker selecionado (o `iid` da linha já é o ticker). A GUI guarda `self._ticker_selecionado` e passa a usar esse valor em `_ticker_apresentado()`.

- **Por que não ler a seleção ao vivo da tabela:** `update()` reconstrói as linhas e zera a seleção; um estado na GUI permite reaplicar a seleção após a recarga e manter o ticker analisado estável.
- **Alternativa descartada:** manter `_evolution_ticker` como "pin" e adicionar mais um caminho — perpetuaria as duas fontes.

### 2. Deduplicar o callback dos dois Treeviews espelhados
`_espelhar_selecao` já usa o guard `_syncing_selection`. O callback de seleção deve ser disparado apenas a partir da árvore de origem (ou sob o guard), para não notificar duas vezes por clique.

### 3. Auto-seleção e preservação após `update()`
Após `update()`, a GUI chama uma rotina que:
- se há `_ticker_selecionado` ainda presente nas linhas, re-seleciona-o;
- senão, seleciona a primeira linha, se existir;
- se não há linhas, limpa `_ticker_selecionado` e não seleciona nada.

Isso atende aos cenários "Seleção inicial automática", "Sem dados não há ticker analisado" e "Seleção preservada após recarga".

### 4. Ocultar abas pulando nomes fora de `ENABLED_TABS`
`_build_ticker_tabs` passa a ignorar (não adicionar) sub-abas cujo nome não está em `ENABLED_TABS`, em vez de adicioná-las com `state="disabled"`. `TAB_CONFIGS` permanece como registro ordenado; as changes dedicadas tornam as abas visíveis adicionando o nome a `ENABLED_TABS` e registrando o painel.

- **Por que não remover de `TAB_CONFIGS`:** as changes futuras dependem desses nomes; mantê-los preserva o contrato.
- **Efeito colateral:** o ramo `else` (placeholder `tk.Text`) e o dicionário `_ticker_indicator_frames` (write-only) ficam mortos; podem ser removidos como limpeza.

### 5. `_do_update` usa `_ticker_apresentado()` para todos os gráficos por ticker
Os três gráficos que hoje usam `_get_selected_ticker()` passam a usar `_ticker_apresentado()`. `_get_selected_ticker()` permanece apenas para a "Análise Geral" (fallback do CSV bruto).

### 6. Duplo-clique mantido como atalho de navegação
`_on_fundamental_row_activated` deixa de fixar `_evolution_ticker` (a seleção já define o ticker) e passa a apenas navegar para "Análise do Ticker" → "Evolução dos Fundamentos".

### 7. `_on_ticker_edit` não mexe mais no ticker analisado
A edição/seleção da TickerList continua disparando `_on_ticker_edit` para refiltrar dados e atualizar o painel corrente, mas não limpa nem altera o ticker selecionado.

## Risks / Trade-offs

- [Callback de seleção disparar duas vezes pelas árvores espelhadas] → disparar apenas da árvore de origem, sob o guard `_syncing_selection`.
- [Seleção perdida em `update()`] → reaplicar a seleção guardada após reconstruir as linhas.
- [`last_subtab` salvo apontar para aba agora oculta] → `_select_tab` falha em silêncio e o notebook permanece na primeira aba; comportamento aceitável.
- [Ticker com fundamentos mas sem dados B3] → os gráficos exibem estado vazio; sem tratamento especial nesta mudança.
- [Conflito de ordem com `diagnosis-panel`] → decisão registrada: "Evolução dos Fundamentos" permanece em primeiro e "Documentos" em último; a change `diagnosis-panel` deverá ser ajustada quando for implementada (o futuro "Diagnóstico" não pode assumir a primeira nem a última posição).
- [Testes que assumem `_evolution_ticker`/fonte pela TickerList] → atualizar os testes de apresentação listados em `tasks.md`.

## Migration Plan

Sem migração de dados. Apenas estado de UI: `last_subtab` pode apontar para aba oculta e cai no fallback da primeira aba. Rollback é o revert dos arquivos de apresentação.

## Open Questions

Nenhuma pendente que altere specs, abordagem ou tarefas.
