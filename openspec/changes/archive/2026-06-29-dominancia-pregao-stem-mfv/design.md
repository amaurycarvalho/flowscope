## Context

O `DominanceRankingChart` (Análise Geral) e o `DominanceTimelineChart` (Análise do Ticker) atualmente usam círculos (`ax.scatter`) no final das barras de CLV para representar o MFV (Money Flow Volume). O tamanho do círculo é `s = max(√(|mfv|/max_mfv) × 120, 8)` em pontos².

Os labels dos tickers são posicionados fixamente em `CLV ± 0.02`, independentemente do círculo. Os textos "Vendedores" e "Compradores" estão em `y=-0.02` (transAxes), desalinhados verticalmente do xlabel "CLV".

O `DominanceTimelineChart` tem os mesmos textos de Vendedores/Compradores em `y=-0.06`.

## Goals / Non-Goals

**Goals:**
- Substituir o círculo de MFV por um stem horizontal (linha) partindo de x=0 na direção do CLV, com comprimento linear proporcional ao MFV
- Usar o mesmo cálculo de proporcionalidade do círculo atual (`√(|mfv|/max_mfv)`) aplicado a `stem_max_len` em data coordinates
- Posicionar o label do ticker após o stem (ou após o CLV, o que se estender mais)
- Truncar stems que ultrapassem `xlim` mas garantir visibilidade do label
- Mover "Vendedores" e "Compradores" para `y=-0.08` no ranking e `y=-0.10` no timeline
- Atualizar texto de orientação em `app.py`
- Manter a supressão para MFV zero ou CLV próximo de zero

**Non-Goals:**
- Não alterar cálculo de MFV, CLV, ou qualquer indicador
- Não alterar layout geral do painel, toolbar, ou tooltip
- Não alterar cores, classificação de dominância, ou eixos
- Não alterar comportamento do gráfico de timeline além da substituição círculo→stem e ajuste de labels

## Decisions

### D1: Stem desenhado com `ax.hlines` vs `ax.plot`

- **Decisão**: Usar `ax.hlines(y, xmin, xmax, ...)` para desenhar o stem.
- **Alternativa considerada**: `ax.plot([x0, x1], [y, y], ...)`.
- **Rationale**: `hlines` é semanticamente mais claro para linhas horizontais e aceita listas (vetorizado), permitindo desenhar todos os stems em uma única chamada. Também lida naturalmente com clipping.

### D2: Stem parte de x=0 (centro) vs da ponta da barra

- **Decisão**: Stem parte de x=0, estendendo-se até `CLV + stem_len` (direção do CLV).
- **Rationale**: O usuário explicitamente pediu "começa na parte central do gráfico - posição x zero - e se estende na direção que o CLV se estende exibido em cima dele". Isso cria uma linha que cruza a barra inteira e se estende além, funcionando como uma "extensão" visual da barra proporcional ao MFV.
- Visualmente: `▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬────` onde `────` é o stem.

### D3: Mapeamento de `s` (pontos²) para data coordinates

- **Decisão**: Calcular `stem_len` proporcional ao diâmetro equivalente do círculo atual.
- **Fórmula**: `stem_len = √(|mfv| / max_mfv) × stem_max_data`
- **Onde `stem_max_data`**: O círculo máximo tem `s=120`. Diâmetro aprox. = `2 × √(120/π) ≈ 12.4 pt`. A 100dpi com axes width ~4 pol (400 px) para 2.4 unid dados: 166.7 px/unid. 12.4 pt × 1/72 pol/pt × 100 px/pol = 17.2 px → 17.2/166.7 ≈ 0.103 unid dados.
- Portanto `stem_max_data ≈ 0.10`. Usar `stem_max_data = 0.10` e `stem_min_data = 0.015` (equivalente ao diâmetro mínimo de `s=8`).
- **Código**:
  ```python
  norm = abs(mfv) / max_mfv if max_mfv > 0 else 0
  stem_len = math.sqrt(norm) * 0.10 if norm > 0 else 0
  stem_len = max(stem_len, 0.015)  # tamanho mínimo visível
  ```

### D4: Label do ticker posicionado após o stem

- **Decisão**: Calcular `label_x = clv + stem_len + 0.02` (CLV positivo) ou `label_x = clv - stem_len - 0.02` (CLV negativo).
- **Rationale**: O label deve ficar após o stem para nunca sobrepor. O offset de 0.02 é um padding visual consistente com o atual.
- Se o stem for truncado por xlim, o label ainda deve ser posicionado no limite do stem truncado (ou no próprio xlim com padding).

### D5: Truncamento de stems

- **Decisão**: Usar clipping automático do matplotlib (default). O stem será truncado visualmente se ultrapassar xlim.
- **Para labels**: Se `label_x` calculado ultrapassar xlim, posicionar o label em `xlim - 0.02` com `ha="right"` para garantir visibilidade.
- **Rationale**: O clipping do matplotlib já impede que o stem seja desenhado fora da área visível. Apenas o label precisa de tratamento explícito.

### D6: Vendedores/Compradores movidos para y=-0.08

- **Decisão**: `y=-0.08` no `DominanceRankingChart` e `y=-0.10` no `DominanceTimelineChart`.
- **Rationale**: O xlabel "CLV" fica tipicamente entre y=-0.06 e y=-0.10. -0.08 alinha no ranking (que é mais compacto). -0.10 no timeline (que já usava -0.06, então -0.10 desce mais para alinhar com o xlabel).
- **Impacto**: Apenas alterar o parâmetro `y` nas chamadas `ax.text()`.

### D7: Stems no DominanceTimelineChart

- **Decisão**: Mesma lógica de stem, porém usando MFV diário (`daily_money_flow`) em vez de acumulado.
- **Rationale**: Consistência visual entre os dois charts. O timeline já tem um eixo secundário para eficiência; o stem substitui o círculo diário.
- **Ajuste**: O timeline tem menos barras e mais espaço horizontal, então `stem_max_data = 0.15` (maior) pode ser adequado.

### D8: Cor do stem

- **Decisão**: Stem em tom de cinza derivado do `score` da classificação (0 a 3). Mapeamento: score 0 → `#C0C0C0` (cinza claro), score 1 → `#555555` (cinza escuro), score 2 → `#222222` (preto escuro), score 3 → `#0A0A0A` (quase preto). `linewidth=2`, `zorder=5`.
- **Alternativa considerada**: Mesma cor da barra; preto sólido; preto tracejado; cinza com luminance igual à cor da barra.
- **Rationale**: O usuário testou visualmente e preferiu que o stem fosse preto mas com tom variando conforme a intensidade da dominância — mais claro para equilíbrio, mais escuro para extremos. O `score` da classificação (0–3) mapeia diretamente para 4 níveis de cinza.

### D9: ToolbarBR — botões Mover e Ampliar mutuamente exclusivos

- **Decisão**: Sobrescrever `pan()`, `zoom()`, `home()`, e `_update_buttons_checked()` em `ToolbarBR` para que os botões Mover e Ampliar funcionem como botões de rádio (apenas um ativo por vez). "Início" desmarca ambos.
- **Rationale**: O comportamento padrão do matplotlib permite ambos ativos simultaneamente, o que confunde o usuário. A implementação usa `self.mode` (enum `_Mode`) e `_update_buttons_checked()` para sincronizar os Checkbuttons do Tk.
- **Detalhe**: `_update_buttons_checked()` foi sobrescrito porque o matplotlib busca os botões por `'Pan'` e `'Zoom'` (inglês), mas a toolbar usa os rótulos em português `'Mover'` e `'Ampliar'`.

## Non-Goals (atualizado)

- ~~Não alterar cores, classificação de dominância, ou eixos~~ → **Cor do stem** foi alterada para cinza (não afeta as barras de CLV)
- ~~Não alterar comportamento do gráfico de timeline além da substituição círculo→stem e ajuste de labels~~ → **Toolbar** foi alterada (comportamento compartilhado entre todos os charts)

## Risks / Trade-offs

- **[R1] Stem pode ser confundido com a barra**: Como o stem parte de x=0 e a barra também, pode não haver distinção visual clara entre barra e stem.
  - **Mitigação**: O stem é desenhado com `linewidth=2` (mais fino que a barra que tem `height=0.6`) e cor em tom de cinza (diferente da barra colorida). A diferença de cor e espessura distingue os dois elementos.

- **[R2] Stem muito curto para CLV pequeno**: Para `|CLV| < 0.05` o stem é suprimido. Para CLV pequeno mas MFV grande, o stem pode parecer desproporcional.
  - **Mitigação**: Aceitável — o stem comunica capital envolvido, não intensidade. Um MFV grande com CLV pequeno é um caso legítimo (muito dinheiro, pouca convicção).

- **[R3] Timeline: stem + eficiência podem sobrepor**: A linha de eficiência (azul, alpha reduzido) cruza o gráfico. Se o stem na ponta da barra colidir com a linha de eficiência, a leitura pode ser prejudicada.
  - **Mitigação**: Stem tem `zorder=5` (acima da barra), eficiência tem `zorder=4`. Se houver colisão, ajustar zorders ou reduzir alpha da eficiência.

- **[R4] Labels truncados em CLV extremo**: CLV perto de ±1.0 pode fazer o label ficar fora da área visível.
  - **Mitigação**: Lógica de fallback: se `label_x` calculado > xlim, usar `xlim - 0.02` com `ha="right"`.

## Open Questions

- `stem_max_data = 0.10` no ranking é um chute inicial. Pode precisar de ajuste fino após inspeção visual com dados reais.
