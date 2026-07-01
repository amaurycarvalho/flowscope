## Context

O painel "Amplitude de Preço" (sub-aba da "Análise do Ticker") usa 4 sub-gráficos matplotlib empilhados com GridSpec 4×1:

1. **Price Range Timeline** (height_ratio=3) — Y=datas (reverso), X=0-100% normalizado. Scatter + plot + setas.
2. **Range % Histórico** (height_ratio=1) — X=datas (cronológico), Y=Range %. Linha do tempo convencional.
3. **Eficiência Diária** (height_ratio=0.5) — gauge horizontal único, só o último dia.
4. **CLV** (height_ratio=0.5) — gauge horizontal único, só o último dia.

Os eixos entre (1) e (2) são transpostos (datas no Y vs. datas no X), impossibilitando correlação visual direta entre posição no range e amplitude relativa. Os gauges (3) e (4) mostram apenas o último pregão, ignorando a série histórica.

A mudança é puramente interna ao `PriceRangePanel` — sem impacto em domínio, estratégias, dados, API ou outros painéis.

## Goals / Non-Goals

**Goals:**
- Fundir as métricas de posição, amplitude relativa e eficiência num único axes matplotlib
- Alinhar todas as métricas pelo mesmo eixo Y (datas, mais recente no topo)
- Manter o CLV como gauge abaixo do gráfico principal
- Preservar tooltip, classificação, setas de trajetória e demais interações existentes
- Atualizar nomenclatura e texto de orientação

**Non-Goals:**
- Não muda estratégias de cálculo (domain/strategies/)
- Não muda dados de entrada nem formato
- Não muda outros painéis ou abas
- Não introduz novas dependências externas

## Decisions

### Decisão 1: Único axes com 3 layers visuais por row

Cada pregão (row no Y) terá 3 canais visuais no mesmo espaço:

```
0%                  50%                 100%
├────────────────────┼────────────────────┤

Layer 1 (fundo):  ████████████████████████   ← barh: Eficiência
                   comprimento = eff (0-1), cor = verde/amarelo/vermelho

Layer 2 (frente): [---●---M--T-VW---]        ← scatter + plot: Timeline
                   posição = normalized price 0-100%

Layer 3 (●):      ● tamanho variável          ← marker size: Amplitude Relativa
                   s = mapeado de range_pct para [40..200]
```

**Por quê:** Elimina a necessidade de twin axes, sub-plots separados ou qualquer mudança de coordenadas. Três respostas visuais num único scan horizontal.

### Decisão 2: Range % codificado como tamanho do marcador de fechamento (●)

Em vez de stem plot ou barra separada, o tamanho do ● (parâmetro `s` do `scatter`) codifica a amplitude relativa de cada pregão.

```python
min_s, max_s = 40, 200
pcts = [float(v) for v in range_pct_dict.values() if v]
lo, hi = min(pcts), max(pcts) if max(pcts) > min(pcts) else min(pcts) + 0.01
size = [min_s + (v - lo) / (hi - lo) * (max_s - min_s) for v in pcts]
```

**Por quê:** Intuitivo — dias mais voláteis têm bolas maiores. Sem eixo extra. A escala é relativa ao dataset, então a comparação entre dias do mesmo ativo é o que importa.

### Decisão 3: Eficiência como barra de fundo por row

Em vez de gauge único do último dia, cada row ganha uma barra horizontal (`barh`) com comprimento = efficiency e cor nos thresholds existentes (≤0.30 vermelho, 0.30-0.60 amarelo, >0.60 verde).

A barra é desenhada com `zorder=1`, abaixo do timeline (zorder=2+), ocupando a altura inteira da row.

**Por quê:** Mostra a série histórica completa de eficiência (não só o último dia). O fundo colorido cria um padrão visual imediato: sequência de rows verdes = dias direcionais consecutivos.

### Decisão 4: GridSpec reduzido de 4 para 2 rows

```
height_ratios=[3, 0.5], hspace=0.2

gs[0] — axes único: Trajetória no Range (timeline + eficiência fundo + ● size)
gs[1] — axes compacto: CLV gauge (mantido como está)
```

### Decisão 5: Nomenclatura atualizada

| Atual | Novo | Explicação |
|---|---|---|
| Price Range Timeline | **Trajetória no Range** | Mostra onde o preço se posicionou |
| Range % Histórico | *eliminado* | Substituído pelo tamanho do ● |
| Range % | **Amplitude Relativa** | `(Max-Min)/PreçoMédio` |
| Eficiência Diária | Eficiência Diária (mantido) | Fundo colorido por row |

### Decisão 6: Tooltip expandida

A tooltip existente (hover no timeline) ganha a linha `Ampl. Relativa: X.XX%` para cada dia, lida do `range_pct_dict`.

### Decisão 7: Classificação mantida

O badge de classificação ("Pregão Lateral", "Movimento Direcional Forte", etc.) continua no canto superior direito, calculado com os mesmos critérios (Range % vs mediana + eficiência).

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| **Densidade visual alta** com layers sobrepostas | A barra de eficiência é semitransparente ou usa cores suaves (alpha=0.3-0.5) para não competir com os marcadores |
| **● muito pequeno ou grande** dependendo da distribuição de Range % | Usar clamping nos percentis 5-95 em vez de min-max bruto para evitar outliers distorcerem a escala |
| **Perda da escala absoluta do Range %** (não dá mais para saber se 2% ou 3% sem tooltip) | Tooltip mostra o valor exato. O badge de classificação também usa o valor numérico internamente |
| **Barra de eficiência confundida com o range normalizado** | A barra tem altura maior (quase toda a row) e cor, enquanto o range é uma linha fina cinza. São visualmente distintas |
