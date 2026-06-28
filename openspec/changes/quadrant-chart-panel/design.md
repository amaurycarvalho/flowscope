## Context

O FlowScope atualmente possui um placeholder "Em desenvolvimento." na sub-aba "Quadrantes" da "Análise Geral". O único gráfico implementado é o `VWAPHistChart` (violin plot), que estabelece o padrão de chart matplotlib + FigureCanvasTkAgg + ToolbarBR. Existem 19 indicadores registrados no DAG engine, incluindo CLV e VWAP.

O painel "Quadrantes" foi concebido para responder simultaneamente a três perguntas:
1. **Quem dominou o fechamento?** — eixo X (CLV)
2. **O preço está acima ou abaixo do VWAP?** — eixo Y (VWAP Distance)
3. **Quanto capital sustentou esse comportamento?** — tamanho da bolha (sqrt fin_instr_qty)

Decisões de design já tomadas na fase de exploração:
- Eixo Y com escala automática simétrica (como o VWAPHistChart já faz)
- Cor com colormap divergente contínuo (RdYlGn ou coolwarm) mapeado ao CLV
- Dias anteriores como setas (quiver), dia mais recente como bolha
- `vwap_distance` como indicador formal registrado no DAG
- Resumo textual automático baseado em regras (contagem por quadrante)

## Goals / Non-Goals

**Goals:**
- Substituir o placeholder "Em desenvolvimento." por um gráfico de dispersão funcional
- Criar e registrar o indicador `vwap_distance` no DAG engine
- Exibir trajetória temporal de cada ativo (setas dos dias anteriores) convergindo para a bolha do último dia
- Usar colormap divergente para codificar o CLV na cor das bolhas
- Usar `sqrt(fin_instr_qty)` para dimensionar as bolhas
- Escala automática simétrica no eixo Y (percentual)
- Tooltip ao passar o mouse mostrando ticker, CLV, VWAP distance, volume, data
- Atualizar o OrientationPanel com texto explicativo + resumo automático por quadrante
- Atualizar `panels.md` e `indicators.md`

**Non-Goals:**
- Animar os dados dia a dia (play/pause) — pode ser futuro, mas não agora
- Exibir todos os 7 dias simultaneamente como bolhas independentes — optou-se por quiver + bolha final
- Gráfico interativo além de hover e toolbar padrão matplotlib (zoom, pan, salvar, copiar)
- Exportação dos dados do gráfico (já existe o botão "Copiar Dados" genérico)

## Decisions

### D1: VWAP Distance como indicador formal no DAG

| Alternativa | Prós | Contras |
|---|---|---|
| **Indicador formal** (`VWAPDistanceStrategy`) | Testável unitariamente, disponível nas abas de texto e export, segue o padrão arquitetural | Mais arquivos, registro extra |
| Cálculo inline no chart | Simples, sem novo arquivo | Não testável isoladamente, não reusável |

**Decisão**: Criar `VWAPDistanceStrategy` no DAG. O indicador depende de `["vwap"]` e computa `(last_price - daily_vwap) / daily_vwap` por ticker-por-data. A implementação segue o padrão exato de `CLVStrategy`.

### D2: Quiver + bolha para representação temporal

A visualização mostra **setas (quiver)** conectando os dias anteriores de cada ticker, convergindo para a **bolha** do dia mais recente.
- A cauda da seta está no (CLV do dia anterior, VWAP distance do dia anterior)
- A ponta da seta está no (CLV do dia atual, VWAP distance do dia atual)
- A bolha (scatter) marca apenas o último dia de cada ticker

Isso permite ver a trajetória sem poluir visualmente com múltiplas bolhas por ticker.

### D3: Escala automática simétrica no eixo Y

Mesma lógica do `VWAPHistChart`: calcular `max_abs = max(abs(min_y), abs(max_y))` e usar `ylim = (-max_abs * 1.1, max_abs * 1.1)`. Isso mantém comparabilidade entre dias sem cortar outliers.

### D4: Colormap divergente contínuo

Usar `matplotlib.colormaps["RdYlGn"]` mapeando CLV de -1 (vermelho) a +1 (verde), com CLV=0 em amarelo. Alternativa considerada: coolwarm (azul-vermelho), menos intuitivo para compra/venda. RdYlGn é mais natural: verde = compra, vermelho = venda.

### D5: Resumo textual por regras

Contar quantas bolhas caem em cada quadrante e aplicar templates:
- Maioria em Q1 → "predominância de ativos com fechamento acima do VWAP e forte pressão compradora"
- Maioria em Q3 → "maioria dos ativos encerrou abaixo do VWAP com pressão vendedora dominante"
- etc.

O resumo é concatenado ao texto de orientação existente no `OrientationPanel`.

### D6: Reaproveitamento do padrão VWAPHistChart

O `QuadrantChart` segue a mesma estrutura:
- Construtor recebe `parent` e `copy_chart_callback`
- `frame` attribute (tkinter Frame)
- `update(data)` — recebe `dict` do `AnalyzeTickersUseCase.execute()`
- `get_figure()` — retorna a Figure para clipboard
- Usa `ToolbarBR` para navegação
- Hover via `motion_notify_event`

## Risks / Trade-offs

- [**Performance**] Com muitos tickers (50+), as setas quiver podem poluir o gráfico. Mitigação: aplicar o filtro do TickerList; o gráfico só exibe os tickers filtrados.
- [**Legibilidade**] Setas sobrepostas podem ser difíceis de distinguir. Mitigação: alpha baixo (0.3-0.5) nas setas, bolha do último dia com alpha=0.8.
- [**Clareza do colormap**] RdYlGn pode ser confundido com sinalização binária (verde = bom, vermelho = ruim), mas CLV > 0 é objetivamente compra e CLV < 0 é venda, então o mapeamento é semanticamente correto.
- [**Manutenção**] Novo indicador `vwap_distance` aumenta a superficie de testes. Mitigação: testar com padrão existente (seguir `TestCLVStrategy`).
