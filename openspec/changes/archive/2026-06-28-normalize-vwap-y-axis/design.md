## Context

O gráfico VWAP (`vwap_hist.py`) exibe múltiplos tickers lado a lado com violinos representando a distribuição de TradAvrgPric, errorbar para MinPric/MaxPric centrado no VWAP, e scatter para LastPric. O eixo Y usa preço absoluto (R$), o que faz com que tickers de preços muito diferentes (ex: R$ 5 e R$ 500) sejam comprimidos visualmente.

A transformação proposta normaliza o eixo Y para `(preço - VWAP) / VWAP × 100`, centralizando todos os tickers em 0% e permitindo comparação direta.

## Goals / Non-Goals

**Goals:**
- Eixo Y exibe desvio percentual do VWAP (%), não preço absoluto
- Violino, errorbar e scatter usam a mesma escala normalizada
- Linha de base horizontal em 0% (VWAP)
- Eixo Y com limites simétricos para representação visual justa
- Tooltip mostra delta % + valor absoluto de referência
- Bucket size adaptado para ranges percentuais

**Non-Goals:**
- Não alterar o cálculo de VWAP, indicadores ou entidades de domínio
- Não alterar a estrutura de dados passada para o chart
- Não adicionar modo toggle (absoluto vs percentual) — a normalização é o novo comportamento padrão
- Não alterar o comportamento do hover para outros charts

## Decisions

### D1: Escala percentual em vez de diferença absoluta (R$)

**Decisão:** Usar `(preço - VWAP) / VWAP × 100`.

**Alternativa considerada:** Diferença absoluta `preço - VWAP` em reais.

**Rationale:** A diferença absoluta ainda sofre do mesmo problema — um desvio de R$ 1 em um ativo de R$ 5 (20%) versus R$ 1 em um ativo de R$ 500 (0,2%) colocaria o primeiro muito mais distante do zero, distorcendo a comparação. A escala percentual normaliza tanto a posição quanto a magnitude dos desvios.

### D2: Substituir `errorbar` por `vlines` + scatter

**Decisão:** Remover `ax.errorbar()` e usar `ax.vlines()` para a barra MinPric–MaxPric + `ax.scatter()` para o marcador VWAP em 0%.

**Alternativa considerada:** Manter `errorbar` com centro em 0.

**Rationale:** `errorbar` usa `yerr = [lower, upper]` onde lower/upper são comprimentos (sempre positivos). Se MinPric > VWAP (raro mas possível), lower seria negativo para alcançar `min_price - vwap > 0`, o que matplotlib trata como extensão para cima, confundindo a lógica. `vlines` aceita coordenadas Y arbitrárias (positivas e negativas), é semanticamente mais claro e lida corretamente com todos os casos.

### D3: Limites simétricos no eixo Y

**Decisão:** `max_abs = max(abs(ylim_min), abs(ylim_max))` seguido de `ax.set_ylim(-max_abs * 1.1, +max_abs * 1.1)`.

**Rationale:** Sem simetria forçada, matplotlib pode mostrar, por exemplo, -2% a +5%, fazendo o zero parecer descentralizado e distorcendo a percepção de "equilíbrio" entre positivo e negativo.

### D4: Bucket size baseado em range percentual

**Decisão:** Nova heurística em `_estimate_bucket_size` para ranges percentuais:
- range ≤ 0.5% → bucket 0.01%
- range ≤ 2% → bucket 0.05%
- range ≤ 10% → bucket 0.25%
- range > 10% → bucket 0.50%

**Rationale:** O range percentual típico fica entre 0,5% e 10%. A granularidade de 0,01% para ranges muito estreitos garante forma suave do violino.

### D5: Tooltip com delta % + preço absoluto

**Decisão:** O hover mostra delta % e preço absoluto lado a lado.

**Rationale:** O delta % é o que importa para comparação, mas o operador ainda precisa saber o preço absoluto para tomar decisões de compra/venda. Exibir ambos evita ter que fazer conta mental.

## Data Flow

```
AnalyzeTickersUseCase.execute()
  │
  └─ data = { ticker: { vwap: { period_vwap }, daily_data: [...], ... } }
     │
     ▼
VWAPHistChart.update(data)
  │
  ├── Para cada ticker: vwap = period_vwap
  │
  ├── daily_data[*].avg_price  →  (avg_price - vwap) / vwap * 100
  ├── daily_data[*].min_price  →  global min → (min - vwap) / vwap * 100
  ├── daily_data[*].max_price  →  global max → (max - vwap) / vwap * 100
  ├── daily_data[*].last_price →  (last - vwap) / vwap * 100  (último dia)
  │
  ├── vwap_idx = 0 (todos os tickers)
  │
  └── axhline(y=0, color='gray', ls='--')
```

## Risks / Trade-offs

- **[Display]** Zero division: VWAP nunca é 0 para ativos reais, mas se um ticker tiver VWAP = 0 por dados corrompidos, o cálculo `(price - 0) / 0 * 100` quebra. **Mitigação:** Verificar `vwap == 0` e pular o ticker ou usar fallback.
- **[Precisão]** Bucket size percentual pode gerar muitos buckets para ranges largos. **Mitigação:** O limite de 0.50% para ranges > 10% mantém o número de buckets gerenciável.
- **[Regressão]** Hover tooltips atuais esperam valores de preço absoluto. **Mitigação:** Atualizar `_on_hover` e o texto do `_annot`.
- **[Regressão]** Testes de snapshot ou golden images precisarão ser atualizados. **Mitigação:** Verificar se existem testes visuais; atualizar conforme necessário.

## Open Questions

- Nenhuma no momento.
