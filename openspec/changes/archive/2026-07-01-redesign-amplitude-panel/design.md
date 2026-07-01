## Context

A aba "Amplitude de Preço" atualmente exibe indicadores como texto puro (Range, Typical Price, etc.) e está desabilitada. O domain layer já possui todos os indicadores necessários (Range, Range%, Typical Price, Median Price, Weighted Close, CLV, Daily Efficiency) com dados por data. O `daily_data` de cada ticker contém `min_price`, `max_price`, `last_price`, `avg_price` por pregão. A reformulação é puramente de apresentação — nenhum novo cálculo de domínio é necessário.

## Goals / Non-Goals

**Goals:**
- Substituir o texto da aba por um painel matplotlib com 4 subplots integrados
- Criar o Price Range Timeline Chart como subplot principal (Y=temporal, X=range normalizado)
- Adicionar Range % histórico como linha temporal
- Adicionar gauges horizontais de Eficiência e CLV
- Adicionar classificação qualitativa como annotation
- Habilitar a aba e atualizar o texto de orientação

**Non-Goals:**
- Não alterar a lógica de indicadores existente
- Não consolidar ou remover outras abas (Eficiência do Movimento, Fluxo Financeiro)
- Não implementar resumo textual automático

## Decisions

### 1. Arquitetura: Classe única PriceRangePanel em charts/

Nova classe `PriceRangePanel` em `src/flowscope/presentation/gui/charts/price_range_panel.py`, seguindo o padrão das classes existentes (`QuadrantChart`, `DominanceTimelineChart`, `DominanceRankingChart`).

**Alternativa considerada:** Componentes separados por arquivo. Rejeitado porque os 4 subplots compartilham dados e layout — uma classe única com gridspec é mais coesa.

### 2. Layout: Figure única com GridSpec

```
┌──────────────────────────────────────────┐
│  Price Range Timeline       [Classificação]│  ← gridspec[0] weight 3
├──────────────────────────────────────────┤
│  Range % Histórico                       │  ← gridspec[1] weight 1
├──────────────────────────────────────────┤
│  Eficiência  [████████░░]               │  ← gridspec[2] weight 0.5
├──────────────────────────────────────────┤
│  CLV         [████████████]              │  ← gridspec[3] weight 0.5
└──────────────────────────────────────────┘
```

**Decisão:** Usar `GridSpec` com `height_ratios=[3, 1, 0.5, 0.5]` para dar protagonismo ao timeline chart.

### 3. Price Range Timeline — Normalização

Cada dia tem seu range [Min, Max]. Para comparar posições entre dias diferentes, normalizamos:

```
x_pos = (preço − Min_do_dia) / (Max_do_dia − Min_do_dia)
```

O eixo X é rotulado de 0% a 100%, com os valores absolutos de hoje como referência secundária no rodapé.

### 4. Price Range Timeline — Marcadores

- **Dia atual:** Mostra todos os marcadores (M=Median, T=Typical, V=VWAP, W=Weighted Close, ●=Close) com labels
- **Dias anteriores:** Mostram apenas o ● (close) com opacidade reduzida, conectados por setas (→) entre dias consecutivos
- **Decisão:** Marcadores apenas no dia atual para evitar poluição visual, conforme definido na exploração

### 5. Quiver temporal

Setas matplotlib `arrow()` conectando o close de cada dia ao close do dia seguinte. A seta parte da posição X do close do dia N e termina na posição X do close do dia N+1, ambas no eixo Y correspondente a cada data.

### 6. Gauges horizontais

Implementados como `barh` com `fig.subplots()` de altura reduzida. A barra de fundo (cinza claro) cobre toda a extensão; a barra de preenchimento (colorida) vai de 0 até o valor do indicador.

- **Eficiência:** escala 0 a 1. Cor: gradiente vermelho→verde
- **CLV:** escala -1 a +1. Cor: vermelho (negativo) ↔ verde (positivo), centro (0) em cinza

**Alternativa considerada:** Canvas tkinter nativo. Rejeitado para manter consistência com o resto da interface (tudo matplotlib).

### 7. Classificação qualitativa

Anotada via `fig.text()` no canto superior direito do timeline chart. Thresholds:

| Range% | Eficiência | Classificação |
|--------|-----------|---------------|
| ≤ mediana histórica | ≤ 0.30 | Pregão lateral |
| > mediana histórica | ≤ 0.30 | Volatilidade sem direção |
| ≤ mediana histórica | > 0.30 | Movimento consistente |
| > mediana histórica | > 0.30 | Movimento direcional forte |

A mediana histórica é calculada a partir da série de Range% dos últimos 30 pregões.

### 8. Integração com app.py

- Habilitar a aba "Amplitude de Preço" em `enabled_tabs`
- Substituir o `Text` widget pela instância de `PriceRangePanel`
- Atualizar `_update_ticker_indicator_tabs()` para chamar `price_range_panel.update()`
- Atualizar `_tab_content` com o novo texto de orientação

## Risks / Trade-offs

- **[Complexidade visual]** O Price Range Timeline com múltiplos dias pode ficar denso se o período for muito longo (30+ dias). → Mitigação: limitar a 20 pregões por padrão, com opção de configurar.
- **[Performance]** matplotlib com 20+ linhas de dados por ticker é leve. Sem risco.
- **[Legibilidade dos marcadores]** Rótulos M, T, V, W podem se sobrepor se estiverem próximos. → Mitigação: usar `annotate()` com offset automático ou ajuste de espaçamento.
- **[Gauges em matplotlib]** barh em subplots pequenos pode parecer deslocado do estilo do app. → Mitigação: usar cores e fontes que imitam o tema claro padrão.
