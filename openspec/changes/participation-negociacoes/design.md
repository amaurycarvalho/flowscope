## Context

O FlowScope possui os indicadores `average_trade_size` e `average_financial_ticket` implementados em `size.py`, e `trade_density` em `density.py`. A tab "Participação Institucional" existe na GUI (`app.py:245`) mas está desabilitada — seu conteúdo é renderizado como texto cru em um `tk.Text`.

O painel precisa ser reformulado para:
1. Renomear para "Participação nas Negociações"
2. Substituir o texto por um painel visual com gauge, cards e timeline
3. Classificar o grau de concentração baseado no histórico do próprio ativo

A arquitetura atual fornece todos os dados necessários via `all_indicators` — cada indicador retorna `dict[date, Decimal]` para todas as datas processadas (Fibonacci, até 21 pregões). O painel pode computar z-scores e percentis diretamente desses dados.

## Goals / Non-Goals

**Goals:**
- Renomear a tab "Participação Institucional" para "Participação nas Negociações"
- Criar `ParticipationPanel` em `presentation/gui/charts/participation_panel.py`
- Implementar gauge horizontal do Índice de Concentração (score 0-1 combinando ATS + AFT normalizados por z-score histórico)
- Implementar card informativo com AFT (R$) e ATS (ações/negócio) e variação vs mediana histórica
- Implementar timeline do AFT nos últimos pregões com linha da mediana
- Implementar classificação qualitativa (Muito Fragmentado a Muito Concentrado) via z-score
- Ativar a tab na interface
- Incluir Trade Density como qualificador textual em tooltips/sumário

**Non-Goals:**
- Não criar novo indicador no engine (a classificação é feita no panel)
- Não modificar os indicadores existentes (`average_trade_size`, `average_financial_ticket`, `trade_density`)
- Não criar visão geral do pregão (apenas por ticker — "Análise do Ticker")
- Não modificar outras tabs ou painéis existentes
- Não adicionar dependências externas

## Decisions

### 1. Classificação no panel, não no engine

A classificação por z-score depende da distribuição histórica de cada ticker. O engine processa cada pregão independentemente e não tem noção de "histórico". O panel já recebe `all_indicators` com todas as datas — ele pode calcular média, desvio padrão e z-score.

**Alternativa considerada:** Criar uma estratégia `concentration_score` no engine. Rejeitada porque a estratégia não teria acesso ao histórico completo de forma limpa — o engine processa os trades de uma vez e não mantém estado entre execuções.

### 2. Score combina ATS e AFT com pesos iguais

```
ats_z = (ats_atual - mean_ats) / std_ats
aft_z = (aft_atual - mean_aft) / std_aft
score = (clip(ats_z, -3, 3) + clip(aft_z, -3, 3)) / 6 + 0.5
       → mapeado para [0, 1]
```

O score 0-1 alimenta o gauge. A classificação usa thresholds no z-score.

**Alternativa considerada:** Usar apenas AFT como indicador principal. Rejeitada porque o ATS (independente de preço) é mais estável ao longo do tempo. A combinação dos dois dá robustez — se o preço subiu muito, o AFT pode disparar, mas o ATS modera.

### 3. Classificação por z-score, não percentis

Com ~21 pontos, percentis extremos (P10, P90) são instáveis (equivalem ao 2º menor/maior valor). Z-score com clipping em ±3 é mais robusto com amostras pequenas.

```
z > 1.5  → Muito Concentrado
z > 0.8  → Concentrado
-0.8 ≤ z ≤ 0.8 → Equilibrado
z < -0.8 → Fragmentado
z < -1.5 → Muito Fragmentado
```

### 4. Timeline exibe apenas AFT

O AFT (em R$) é mais intuitivo para o usuário acompanhar ao longo do tempo. O ATS aparece apenas no card e no tooltip. A linha horizontal da mediana do período contextualiza o valor atual.

**Alternativa considerada:** Duas linhas (AFT + ATS normalizado). Rejeitada por poluição visual — os indicadores são correlacionados e a informação duplicada não justifica a complexidade.

### 5. Trade Density como qualificador textual

Trade Density não entra no score porque sua fórmula (`TradesQty / Range`) introduz sensibilidade à volatilidade que não é comparável entre ativos. No entanto, é útil para qualificar a interpretação:

- Se ATS alto + Trade Density alto → "poucos negócios grandes, mas fragmentados por faixa de preço"
- Se ATS alto + Trade Density baixo → "poucos negócios grandes e concentrados"

### 6. Layout do painel

```
GridSpec: 3 rows
  row 0 (height_ratio 3): Gauge horizontal + card informativo lado a lado
  row 1 (height_ratio 2): Texto de classificação e sumário
  row 2 (height_ratio 4): Timeline do AFT
```

O gauge ocupa a esquerda, o card a direita na mesma linha.

### 7. Tratamento de bordas

- Se std histórico = 0 (ativo sem variação de ATS): usar threshold nominal (ex: ATS > 5000 ações = concentrado)
- Se apenas 1 data disponível: mostrar valores sem classificação
- Trade Density ausente: omitir qualificador textual, não quebrar

## Risks / Trade-offs

- **Dados insuficientes para z-score**: Com menos de 3 pregões, o desvio padrão é zero ou instável. Mitigação: fallback para thresholds nominais ou exibição sem classificação.
- **Correlação ATS/AFT**: Como AFT = ATS × Preço, os dois indicadores não são independentes. O score duplica a informação, mas isso é mitigado porque o z-score de cada um é calculado sobre sua própria distribuição histórica — se o preço subiu, a distribuição do AFT também subiu, e o z-score reflete o desvio da nova normalidade.
- **Desempenho**: O painel precisa percorrer o histórico de indicadores para cada ticker. Com ~21 datas e ~100 tickers, isso é irrelevante.
- **Trade Density não entra no score**: Pode dar a impressão de que ignoramos fragmentação. Clarificar no texto de orientação que o painel mede concentração de capital, não de atividade.
