## Context

Ver `proposal.md - Why`. Hoje `FundamentalTablePanel` (`presentation/gui/charts/fundamental_table.py`) possui um único `ttk.Treeview` com as 26 colunas de `_COLUNAS`, uma barra de rolagem vertical e uma horizontal. As larguras são lidas por `get_column_widths()` e persistidas em `_prefs["fundamental_column_widths"]` (`app.py`, `app_tab_layout.py`). O CSV é montado por `montar_csv()` a partir de `_fundamental_data`, sem qualquer leitura dos widgets (`app_csv.py`). Não há binding de `<<TreeviewSelect>>`; a seleção é apenas visual.

Restrições relevantes: `montar_linhas`/`montar_csv` devem permanecer intactos para não afetar a exportação; as larguras persistidas continuam indexadas por identificador estável de coluna; a preferência antiga deve continuar válida e ser a única fonte de verdade da largura da região congelada.

## Goals / Non-Goals

**Goals:**
- Congelar `Ticker` e `Nome` à esquerda, com as demais 24 colunas rolando horizontalmente.
- Dois Treeviews sincronizados em rolagem vertical e seleção, com a região congelada dimensionada pelas próprias colunas.
- Persistir a largura de todas as colunas (incluindo as congeladas), que define a região congelada.
- Manter a cópia CSV com todas as 26 colunas, sem alteração de formato.

**Non-Goals:**
- Reordenar, adicionar, remover, ordenar ou editar colunas.
- Oferecer um divisor independente para a região congelada; a largura é controlada pelas colunas `Ticker` e `Nome`.
- Alterar o formato ou o conteúdo do CSV.
- Suportar seleção múltipla.

## Decisions

### 1. Dois Treeviews lado a lado com fronteira auto-ajustada (sem `PanedWindow`)
Cada painel contém seu próprio `Treeview` dentro de um frame; a fronteira entre eles é a borda direita da coluna `Nome`, reforçada por um separador vertical fixo e puramente visual (`ttk.Separator`, não arrastável e sem influência sobre a largura). Alternativas: (a) `ttk.PanedWindow` com sash móvel — rejeitada porque cria uma segunda fonte de verdade para a largura da região (o sash) que compete com as larguras das colunas, produzindo gap ou clipping e exigindo uma preferência extra; (b) sobrepor um segundo Treeview sobre as duas primeiras colunas do Treeview principal — rejeitada pela complexidade de manter a sobreposição fixa durante a rolagem horizontal; (c) renderizar as colunas congeladas em um `Canvas` — rejeitada por duplicar a lógica de linhas/headings.

### 2. `_COLUNAS` permanece canônico
Derivar `_COLUNAS_FIXAS = _COLUNAS[:2]` e `_COLUNAS_ROLANTES = _COLUNAS[2:]`. `montar_linhas`, `_linha_analise`, `_linha_sintetica` e `montar_csv` continuam operando sobre a tupla completa de 26 campos. A divisão é puramente de apresentação.

### 3. `iid` estável por linha (ticker)
Inserir cada linha nos dois Treeviews com `iid=ticker`, garantindo identidade entre as linhas para espelhar seleção e rolar. Alternativa: confiar nos `iid` automáticos por ordem de inserção — rejeitada por ser frágil caso a ordem de atualização mude.

### 4. Sincronização de rolagem vertical por fração, com viewports iguais
O `yscrollcommand` do Treeview rolável aciona a barra vertical e move o Treeview congelado via `yview_moveto(first)`; o comando da barra chama `yview(*args)` nos dois; a roda do mouse sobre qualquer painel é encaminhada aos dois. Para evitar deriva de fração, o painel congelado reserva um espaçador inferior da mesma altura da barra horizontal do painel rolável, igualando as alturas de viewport (mesmo número de linhas e mesma altura de linha). Alternativa: sincronizar por índice de linha com `identify_row` — rejeitada por ser mais complexa e sujeita a tremor durante a rolagem.

### 5. Largura do painel congelado derivada das colunas
A largura do frame congelado é a soma das larguras de `Ticker` e `Nome`, aplicada explicitamente (ex.: `frame_congelado.configure(width=soma)` com `propagate(False)`), sem depender da propagação de tamanho do Tk. Ao redimensionar uma coluna congelada, o handler `_on_column_resized` recalcula a soma e ajusta o frame, garantindo a fronteira exatamente na borda de `Nome` (sem gap nem clipping). O frame rolável usa `weight=1` no grid e o congelado `weight=0`. Uma largura mínima para o painel rolável limita o painel congelado quando as colunas crescem demais. Alternativa: divisão proporcional fixa (ex.: 25%) — rejeitada por não acompanhar o resizing das colunas.

### 6. Seleção única espelhada com guarda de reentrância
`selectmode="browse"` nos dois Treeviews. No evento `<<TreeviewSelect>>`, ler a seleção de origem e aplicar `selection_set` no outro Treeview, protegido por uma flag de reentrância para evitar loop. Isso desabilita multi-seleção.

### 7. Persistência de larguras agregada, mesmo formato
`get_column_widths()` passa a agregar as larguras dos dois Treeviews em um único dicionário indexado pelo id da coluna; `_on_column_resized` é associado a ambos via `<ButtonRelease-1>`, e `_last_widths` cobre o conjunto agregado. O formato de `fundamental_column_widths` não muda.

### 8. CSV desacoplado dos widgets
`_build_fundamental_csv` continua usando `_fundamental_data` e `montar_csv`; nenhuma alteração é necessária para manter a cópia completa.

### 9. Layout do frame
`frame` em grid com quatro colunas: frame congelado em (0,0) `nsew` com `weight=0` e largura fixada pela soma das colunas, separador vertical fixo em (0,1) `ns` com `weight=0`, frame rolável em (0,2) `nsew` com `weight=1`; barra vertical compartilhada em (0,3) `ns`. Painel congelado: Treeview + espaçador (sem barra horizontal). Painel rolável: Treeview + barra horizontal. A barra horizontal fica apenas sob o painel rolável, pois o congelado não rola horizontalmente. O separador garante que a linha divisória permaneça visível quando o painel rolável rola horizontalmente, já que a borda interna das colunas rola junto com o conteúdo. Alternativa: barra horizontal ocupando a largura total — rejeitada por sugerir rolagem do painel congelado.

## Risks / Trade-offs

- **[Deriva de rolagem vertical]** Frações divergem se as alturas de viewport diferirem → espaçador de altura igual à barra horizontal sob o painel congelado; validar alinhamento visual.
- **[Eventos de roda do mouse multiplataforma]** Linux usa `Button-4/5`; Windows/macOS usam `MouseWheel` → associar ambos e testar no Linux (plataforma alvo).
- **[Colunas congeladas largas engolem o viewport]** `Nome` muito largo reduz o painel rolável → largura mínima para o painel rolável e limite do painel congelado.
- **[Atualização da largura do frame congelado]** Mudanças de largura de coluna podem não propagar o tamanho solicitado do Treeview → recalcular e aplicar a soma explicitamente em `_on_column_resized`, com `propagate(False)`.
- **[Recursão na seleção]** Espelhar seleção dispara o evento no outro Treeview → flag de reentrância.
- **[Testes acoplados ao widget único]** Testes de `TestFundamentalTablePanel` acessam `painel._tree`, `painel._columns` e o índice 15 → expor os dois Treeviews e um acessor agregado; ajustar os testes para os novos índices.

## Migration Plan

1. Nenhuma preferência nova: `fundamental_column_widths` já é carregada e passa a definir a largura do painel congelado.
2. Compatibilidade retroativa: preferências antigas carregam normalmente; sem migração de dados.
3. Rollback: reverter o código; o `config.json` permanece compatível.

## Open Questions

Nenhuma pendente que afete specs, abordagem ou tarefas.
