## Context

A sub-aba "Fluxo Financeiro" existe como placeholder desabilitado (tk.Text com raw indicators). Todos os indicadores necessários já são computados pelo DAG engine: `daily_money_flow` (R$ por dia), `money_flow_volume` (R$ acumulado), `clv`, `buying_pressure`, `selling_pressure`. O painel precisa transformar esses dados em uma visualização que responda se o movimento do preço foi sustentado por capital.

O painel opera no contexto "Análise do Ticker" (um ticker por vez), seguindo o padrão de `PriceRangePanel` e `DominanceTimelineChart`.

## Goals / Non-Goals

**Goals:**
- Criar painel matplotlib com gauge horizontal divergente do Daily Money Flow
- Criar classificador qualitativo baseado em score normalizado (|DMF|/fin_vol) com 5 níveis
- Exibir Buying Pressure vs Selling Pressure como barra empilhada
- Integrar CLV como marcador no próprio gauge principal (sem subplot separado)
- Exibir MFV acumulado como texto sobrescrito no gauge
- Ativar a sub-aba e conectar summary_callback para resumo textual dinâmico

**Non-Goals:**
- Não alterar indicadores existentes (daily_money_flow, money_flow_volume, clv, etc.)
- Não criar novas strategies no DAG engine
- Não modificar outros painéis ou abas existentes
- Não adicionar interatividade de clique (apenas hover tooltip)

## Decisions

### D1: Daily Money Flow como indicador operacional principal

O painel usa `daily_money_flow` (CLV × fin_vol do dia) como indicador principal, não o `money_flow_volume` acumulado. O MFV acumulado vira contexto textual. Essa separação responde diretamente "o movimento de hoje foi sustentado?" enquanto o acumulado responde "como vem sendo o fluxo?"

### D2: Score normalizado para classificação

Em vez de thresholds absolutos em reais (que não funcionam entre PETR4 e small caps), o classificador usa `score = daily_money_flow / fin_vol`. Isso produz um valor comparável entre ativos.

**Thresholds:**

| Score | Classificação |
|---|---|
| > +0,15 | Fluxo Muito Forte (Comprador) |
| +0,08 a +0,15 | Fluxo Forte |
| +0,03 a +0,08 | Fluxo Moderado |
| +0,01 a +0,03 | Fluxo Fraco |
| -0,01 a +0,01 | Neutro |
| -0,03 a -0,01 | Fluxo Fraco (Vendedor) |
| -0,08 a -0,03 | Fluxo Moderado |
| -0,15 a -0,08 | Fluxo Forte |
| < -0,15 | Fluxo Muito Forte (Vendedor) |

Simétrico, independente de capitalização e liquidez.

### D3: CLV integrado como marcador no gauge principal

O CLV está embutido no MFV (MFV = CLV × fin_vol). Em vez de um subplot separado, o CLV aparece como um marcador (triângulo ou linha vertical) sobreposto no gauge, indicando onde ocorreu o fechamento no range. Isso reduz complexidade visual.

### D4: MFV acumulado como texto no gauge

Em vez de subplot separado, o valor acumulado do período aparece como texto de contexto dentro do próprio eixo do gauge, estilo "Acum. 7d: +R$ 52,3M".

### D5: GridSpec de 2 linhas

```
Row 0 (60%): Gauge MFV (divergente) com CLV marker + MFV acumulado + score
Row 1 (40%): Barra empilhada B×S (65%) | Range% + info contexto (35%)
```

Isso maximiza destaque para o indicador principal enquanto ancora com a decomposição do range.

### D6: Summary callback segue padrão Quadrantes

O painel recebe `summary_callback` no construtor e o invoca em `update()` com um texto-resumo em português. O OrientationPanel é atualizado dinamicamente, igual ao Quadrantes.

### D7: MoneyFlowClassifier como novo módulo

Novo arquivo `src/flowscope/domain/strategies/classifiers/money_flow.py` com `@dataclass(frozen=True) MoneyFlowClassification` e função `classify_money_flow(score: float)`. Segue o padrão de `DominanceClassification` e `ConvictionClassification`.

## Risks / Trade-offs

- [Thresholds empíricos] Os thresholds de 1%/3%/8%/15% são propostas iniciais. Podem precisar de calibração após uso real. → Mitigação: o classificador é um módulo isolado; ajustar thresholds não afeta o painel.
- [MFV acumulado em contexto] Se o período tiver poucos dias (ex.: 1 dia), o acumulado = daily. O texto de contexto precisa ser claro: "Acum. 1d: R$ X" em vez de "7 dias".
- [Desempenho] matplotlib em TkAgg com 2 subplots é leve. O painel não deve impactar performance perceptível.
