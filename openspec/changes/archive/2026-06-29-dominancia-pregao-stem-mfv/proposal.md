## Why

O círculo de MFV no ranking de Dominância do Pregão é visualmente ruidoso: a área do círculo é difícil de comparar entre tickers, e a sobreposição com o label do ticker cria poluição visual. Um stem horizontal (traço) partindo do centro do gráfico na direção do CLV comunica o volume financeiro de forma mais limpa e comparável, pois o comprimento linear é mais fácil de julgar do que área.

## What Changes

- **DominanceRankingChart**: Substituir círculo do MFV por stem horizontal que parte de x=0 e se estende na direção do CLV, com comprimento proporcional ao MFV (mesmo cálculo do diâmetro do círculo atual)
- **DominanceTimelineChart**: Mesma substituição (stem no lugar do círculo) para consistência entre os dois charts
- **Label do ticker**: Posicionar após o stem (ou após o CLV, o que se estender mais) para evitar sobreposição
- **Stem truncado**: Se CLV + stem_len ultrapassar xlim, truncar o stem mas garantir que o label do ticker ainda apareça
- **"Vendedores" / "Compradores"**: Mover para y=-0.08 (transAxes) para alinhar com o texto "CLV" do eixo X. Mesma correção no dominance_timeline.
- **Texto de orientação**: Atualizar referência de "círculo" para "traço horizontal" no OrientationPanel da aba Dominância do Pregão
- **MFV próximo de zero**: Manter a supressão atual (`mfv == 0.0 or abs(clv) < 0.05`)
- **ToolbarBR — botões Mover/Ampliar**: Tornar mutuamente exclusivos (desmarcar um ao clicar no outro). Botão "Início" desmarca ambos

## Capabilities

### New Capabilities

Nenhuma — trata-se de refinamento visual de painéis existentes, sem introdução de nova funcionalidade ou indicador.

### Modified Capabilities

Nenhuma — o comportamento em nível de requisito não se altera. O gráfico continua exibindo o ranking de CLV com magnitude de MFV; apenas a codificação visual muda (círculo → stem).

## Impact

- `src/flowscope/presentation/gui/charts/dominance_ranking.py` — Substituir scatter do círculo por hlines/plot do stem; ajustar posição dos labels; mover Vendedores/Compradores
- `src/flowscope/presentation/gui/charts/dominance_timeline.py` — Mesmas alterações para consistência
- `src/flowscope/presentation/gui/charts/toolbar.py` — Mutuamente exclusivos Mover/Ampliar; Início desmarca ambos
- `src/flowscope/presentation/gui/app.py` — Atualizar texto de orientação do painel Dominância do Pregão (Análise Geral)
