## Context

O FlowScope calcula indicadores a partir de dados consolidados da B3. O VWAP atual pondera por NtlFinVol (R$), mas o correto conceitualmente é FinInstrMty (quantidade de ações/contratos). O gráfico VWAP é um bar chart simples do VWAP periódico, sem mostrar distribuição de preços.

Dados diários necessários para o novo gráfico (TradAvrgPric, FinInstrmQty, MinPric, MaxPric, LastPric) existem no `TradeDay` mas não são expostos no resultado do `AnalyzeTickersUseCase`.

## Goals / Non-Goals

**Goals:**
- Alterar o peso do VWAP de NtlFinVol para FinInstrMty em todo o app
- Substituir o bar chart por um violin plot horizontal com perfil de volume (largura ∝ FinInstrmQty) + errorbar (VWAP/Min/Max) + scatter (LastPric recente)
- Expor dados diários adicionais no use case para alimentar o novo gráfico
- Atualizar tooltip do Radiobutton VWAP

**Non-Goals:**
- Alterar CVD, Volume Profile, ou outros indicadores
- Alterar o scatter plot VWAP×CVD ou CVD histogram
- Adicionar novos parâmetros/configurações de indicadores

## Decisions

### 1. Peso do VWAP: NtlFinVol → FinInstrMty

| Alternativa | Voto |
|---|---|
| `Σ(avg_price × fin_vol) / Σ(fin_vol)` | Atual — peso financeiro |
| **`Σ(avg_price × fin_instr_qty) / Σ(fin_instr_qty)`** | **Escolhido — peso por quantidade** |

**Rationale**: O VWAP clássico é preço médio ponderado por volume (quantidade de ações), não por volume financeiro. A B3 fornece ambos, mas FinInstrMty é a grandeza correta.

### 2. Estrutura do resultado do use case

Adicionar chave `"daily_data"` no dict de cada ticker:

```python
result[ticker] = {
    "vwap": { "period_vwap": Decimal, "daily_vwap": {date: Decimal}, "total_fin_instr_qty": int },
    "cvd": { ... },
    "volume_profile": { ... },
    "daily_data": [
        {
            "date": date,
            "avg_price": Decimal,
            "min_price": Decimal,
            "max_price": Decimal,
            "last_price": Decimal,
            "fin_instr_qty": int,
        }
    ],
}
```

**Rationale**: Acoplar os dados brutos ao resultado evita uma segunda consulta ao repositório. O volume de dados é pequeno (≤7 dias × ~30 tickers).

### 3. Visualização do novo gráfico

```
Ticker_A     Ticker_B     Ticker_C
   │            │            │
   │   ┌───┐    │            │
   │   │   │    │   ┌───┐    │
   │   │   │    │   │   │    │
  ─┤───█───█────┼───█───█────┤──  ← VWAP (errorbar center)
   │   │   │    │   │   │    │
   │   │   │   ─┤───█───│────┤──  ← Min/Max (errorbar caps)
   │   │   │    │ █│ █  │    │
   │   │   │    │ █│ █  │    │
   │  ─┤───│────┤ █│ █  │    │
   │   │ █ │    │ █│ █  │    │
   │   │ █ │    │  │ █  │   ─┤
   │   │ █ │    │  │ █  │    │
   │   │ █◊│    │  │ ◈  │    │  ← LastPric (scatter)
   │   │ █ │    │  │ █  │    │
   └───┴───┴────┴──┴───┴────┘
        │              │
        └── violino ← largura ∝ Σ FinInstrmQty por bucket de preço
```

- **Violinplot**: Para cada ticker, agrupar TradAvrgPric diário em buckets (ex: R$0.10). Largura do violino em cada bucket ∝ soma de FinInstrmQty dos dias onde o avg_price cai naquele bucket. Implementado com `fill_between` para controle total sobre o formato.
- **Errorbar**: `matplotlib.axes.errorbar(x=ticker, y=VWAP, yerr=[[VWAP-MinPric], [MaxPric-VWAP]])`, fmt='o', color='black', capsize=4
- **Scatter**: `matplotlib.axes.scatter(x=ticker, y=last_price_recente)` em destaque (cor diferente, ex: vermelho)

### 4. Tooltip do Radiobutton

Substituir o texto atual (`"Preço médio ponderado por volume"`) por uma versão mais curta e informativa:

> "Preço médio ponderado pela quantidade de ativos negociados. Mostra distribuição de preços no período."

### 5. Título do gráfico

`"VWAP — Distribuição de Preços"` (substitui `"VWAP Histogram"`)

## Risks / Trade-offs

- **[Poucos pontos por ticker]** Com janela Fibonacci (≤7 dias), o perfil de volume horizontal terá resolução baixa. → Buckets de preço maiores (R$0.10–R$0.50) podem ser necessários; considerar agrupamento adaptativo.
- **[Mudança do VWAP é breaking]** Testes existentes em `test_domain/test_indicators.py` quebram. → Atualizar valores esperados nos asserts.
- **[Desempenho]** `daily_data` adiciona dados redundantes ao resultado. → Impacto insignificante (poucas dezenas de registros).
