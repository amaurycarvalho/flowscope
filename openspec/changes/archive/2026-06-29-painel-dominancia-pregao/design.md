## Context

O FlowScope possui um engine de indicadores baseado em DAG (Directed Acyclic Graph) que calcula 17+ indicadores por ticker por data. A GUI é construída em Tkinter com matplotlib embedding para gráficos, seguindo um padrão de widget chart (`FigureCanvasTkAgg` + `ToolbarBR` + `update(data)`). Existem dois charts implementados: `VWAPHistChart` (violino) e `QuadrantChart` (dispersão com bolhas).

O painel "Dominância do Pregão" atual na aba Análise do Ticker é um widget de texto que mostra Range, Range%, Typical Price, Median Price, Weighted Close — métricas de amplitude, não de dominância. Os indicadores necessários (CLV, Daily Efficiency, Money Flow Volume) já existem no engine, mas não têm visualização dedicada.

## Goals / Non-Goals

**Goals:**
- Criar dois novos painéis com gráficos de barras divergentes usando matplotlib
- Registrar `daily_money_flow` e `dominance_score` como strategies no engine
- Criar módulo de classificadores desacoplado (`classify_dominance`, `classify_conviction`)
- Renomear o tab "Dominância do Pregão" para "Amplitude de Preço"
- Compartilhar o período temporal implícito (`fibonacci_dates`) com os demais painéis
- Reutilizar o padrão existente de chart widget (FigureCanvasTkAgg + ToolbarBR)

**Non-Goals:**
- Não alterar o engine de indicadores além do registro de novas strategies
- Não adicionar seletor de período explícito (slider/date range) — mantém período implícito
- Não criar painel de Financial Density (será especificado posteriormente)
- Não modificar os painéis VWAP, Quadrantes, Fluxo Financeiro, Participação Institucional, Eficiência ou Resumo Geral
- Não alterar a lógica de carregamento de dados ou o use case

## Decisions

### D1: Novas strategies no engine vs. cálculo no frontend

- **Decisão**: Registrar `daily_money_flow` e `dominance_score` como strategies no IndicatorEngine.
- **Alternativa considerada**: Calcular no frontend a partir de CLV e Daily Efficiency já disponíveis.
- **Rationale**: O usuário explicitamente solicita registro para reuso futuro. Além disso, manter no engine torna os indicadores disponíveis para CLI, export CSV, e eventuais análises estatísticas sem duplicação de lógica.
- `daily_money_flow`: depende de `clv` (precisa do CLV por dia × FinVol do TradeDay). Output: `dict[str, dict[date, Decimal]]`.
- `dominance_score`: depende de `clv` e `daily_efficiency`. Output: `dict[str, dict[date, Decimal | None]]`.

### D2: Classificadores como módulo separado

- **Decisão**: Criar `domain/strategies/classifiers/` como submódulo independente, sem dependência do IndicatorEngine.
- **Alternativa considerada**: Incorporar classificação nas strategies existentes.
- **Rationale**: Classificação é uma transformação de apresentação, não um cálculo de indicador. Separar permite que os painéis usem as funções sem instanciar o engine, e mantém as strategies focadas em computação pura. A estrutura de retorno tipada (`@dataclass`) permite que os charts consumam diretamente sem lógica condicional espalhada.

### D3: Stem no ranking usa MFV acumulado; stem no timeline usa MFV diário

- **Decisão**: O ranking (Análise Geral) usa `money_flow_volume` (acumulado do período) para o stem. O timeline (Análise do Ticker) usa o novo `daily_money_flow` (por pregão).
- **Rationale**: No ranking, cada barra é um ticker — faz sentido mostrar o fluxo total que sustentou a dominância no período. No timeline, cada barra é um dia — o fluxo diário é mais informativo para comparar a evolução. A estratégia `money_flow_volume` já existe; `daily_money_flow` é a nova strategy necessária.

### D4: Eficiência como linha conectada em eixo secundário no timeline

- **Decisão**: A Daily Efficiency será plotada como uma linha conectando os valores de cada pregão, utilizando um eixo Y secundário à direita (0 a 1) no mesmo gráfico matplotlib.
- **Alternativa considerada**: Marcador visual (triângulo/círculo) sobre cada barra sem eixo dedicado.
- **Rationale**: Linha conectada permite enxergar a evolução temporal da convicção. Eixo secundário evita escala ambígua. A sobreposição segue o padrão do mercado financeiro (price + indicator overlay).

### D5: Widgets de chart seguem o padrão existente

- **Decisão**: `DominanceRankingChart` e `DominanceTimelineChart` seguem a mesma interface dos charts existentes: `__init__(parent, *, copy_chart_callback)`, `update(data)`, `frame` attribute, `get_figure()`.
- **Rationale**: Consistência com `VWAPHistChart` e `QuadrantChart`. Facilita integração em `_build_main_area` e `_update_charts`. O `ToolbarBR` é reutilizado para zoom, pan, salvar e copiar.

### D6: Renomeação do tab, não remoção

- **Decisão**: O tab "Dominância do Pregão" existente no Análise do Ticker será renomeado para "Amplitude de Preço". O novo tab "Evolução da Dominância" será adicionado.
- **Rationale**: Preserva o conteúdo existente (Range, Range%, etc.) que tem utilidade própria. Evita remoção de funcionalidade. A renomeação alinha nome ao conteúdo real.

### D7: Mapa de cores divergente para as barras

- **Decisão**: Usar colormap divergente customizado: verde escuro (#1B5E20) → verde claro (#A5D6A7) → cinza (#BDBDBD) → vermelho claro (#EF9A9A) → vermelho escuro (#B71C1C), mapeado aos 7 níveis de classificação.
- **Alternativa considerada**: Colormap RdYlGn do matplotlib.
- **Rationale**: RdYlGn tem amarelo no centro, que visualmente parece "neutro" mas atrai atenção. O cinza no centro reduz noise visual. As cores mais escuras nos extremos comunicam intensidade sem depender de largura de barra.

## Data flow

```
B3 CSV → parse_csv() → list[TradeDay]
    ↓
IndicatorEngine.execute(trades)
    ├── clv                       → dict[ticker][date]
    ├── daily_efficiency          → dict[ticker][date]
    ├── daily_money_flow          → dict[ticker][date]  ★ NEW
    ├── dominance_score           → dict[ticker][date]  ★ NEW
    ├── money_flow_volume         → dict[ticker][Decimal] (acumulado)
    └── ... (demais indicadores)
    ↓
AnalyzeTickersUseCase shapes output
    ↓
FlowScopeGUI._current_data
    ├── DominanceRankingChart.update() 
    │   ← usa: clv (última data), money_flow_volume (acumulado), classify_dominance()
    │
    └── DominanceTimelineChart.update()
        ← usa: clv (série), daily_efficiency (série), daily_money_flow (série),
                classify_dominance(), classify_conviction()
```

## Layout — DominanceRankingChart

```
┌─────────────────────────────────────────────────────┐
│  DOMINÂNCIA DO PREGÃO          Toolbar (zoom, pan)  │
│                                                       │
│         VENDEDORES    │    COMPRADORES                │
│                        │                               │
│                  ◄████ │────  PETR4  +0.82             │
│               ◄█████  │───   VALE3  +0.55             │
│                  ◄███  │──    ITUB4  +0.31             │
│                    ◄█  │─     BBAS3  +0.12             │
│                        │◄─    ABEV3  -0.08             │
│                        │◄───  BBDC4  -0.22             │
│               ◄██████  │────  ELET3  -0.65             │
│                        │                               │
│  -1.0              0.0              +1.0               │
└─────────────────────────────────────────────────────┘
```

## Layout — DominanceTimelineChart

```
┌───────────────────────────────────────────┬────────────┐
│  EVOLUÇÃO DA DOMINÂNCIA — PETR4           │  Resumo    │
│                                           │            │
│  VENDEDORES   │    COMPRADORES            │  Dominância│
│               │                            │  Compra    │
│  20/06  ████████████████►────             │  Forte     │
│  23/06    ████████►────                   │            │
│  24/06  ◄████────                        │  Convicção │
│  25/06  ◄████████────                     │  Alta      │
│  26/06  ████████████████████████►──────  │            │
│               │                            │  Fluxo     │
│               │           ── Eficiência    │  R$ 4.2M   │
│               │            ▁▃▆▇▆▅▃▁       │            │
│               │                            │  Comp.     │
│  -1.0      0.0        +1.0                │  63%       │
└───────────────────────────────────────────┴────────────┘
```

## Risks / Trade-offs

- **[R1] Perda de data de referência ao renomear tab**: O nome do tab "Dominância do Pregão" é usado como chave em `tab_configs` e `_tab_content`. A renomeação exige atualizar todas as referências, incluindo a lógica de `_restore_tabs` que salva `last_subtab`.
  - **Mitigação**: A lógica de restauração usa `notebook.tab(i, "text")`, portanto ao renomear o tab o nome salvo em `last_subtab` no config.json de sessões anteriores não será encontrado. Aceitável — o fallback silencioso em `_restore_tabs` já trata isso.

- **[R2] Performance com muitos tickers no ranking**: O DominanceRankingChart precisa renderizar uma barra por ticker. Com 80+ tickers (IDIV), o matplotlib pode ficar lento.
  - **Mitigação**: Limitar a altura do gráfico a ~30 tickers visíveis com scroll. Alternativamente, usar `ax.barh` que é eficiente para datasets médios. Se necessário, adicionar filtro por top N.

- **[R3] Sobreposição visual entre stem e eficiência**: No timeline, o stem de MFV diário pode colidir visualmente com a linha de eficiência.
  - **Mitigação**: A linha de eficiência é plotada após as barras (zorder maior) com alpha reduzido e cor distinta (azul). Stem tem zorder=5 e cor em tom de cinza.

- **[R4] Stem em CLV próximo de 0**: Quando CLV ≈ 0, a barra tem comprimento próximo de zero, e o stem fica sobre o eixo central.
  - **Mitigação**: Para `|CLV| < 0.05`, não exibir stem (evita poluição visual). MFV pode ser visto no tooltip.

## Open Questions

- Nenhuma no momento. As decisões sobre período, estratégias e layout estão fechadas.
