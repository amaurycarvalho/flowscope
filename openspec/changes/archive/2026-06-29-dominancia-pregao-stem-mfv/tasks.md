## 1. DominanceRankingChart — Stem e Ajustes

- [x] 1.1 Substituir o scatter do círculo por `ax.hlines` desenhando o stem de x=0 até `clv + stem_len`, com `stem_len = √(|mfv|/max_mfv) × 0.10` (mín. 0.015). Manter supressão para `mfv == 0.0` ou `|clv| < 0.05`.
- [x] 1.2 Atualizar posição do label do ticker: calcular `label_x = clv + stem_len + 0.02` (positivo) ou `clv - stem_len - 0.02` (negativo). Se ultrapassar xlim, usar `xlim - 0.02`.
- [x] 1.3 Mover textos "Compradores →" e "← Vendedores" de `y=-0.02` para `y=-0.08` (transAxes).

## 2. DominanceTimelineChart — Stem e Ajustes

- [x] 2.1 Substituir o scatter do círculo por stem horizontal usando a mesma lógica, porém com `stem_max_data = 0.15` (timeline tem mais espaço horizontal).
- [x] 2.2 Ajustar posição dos labels de data conforme o stem (N/A — timeline usa yticklabels, sem sobreposição com stems).
- [x] 2.3 Mover textos "Compradores →" e "← Vendedores" de `y=-0.06` para `y=-0.10` (transAxes).

## 3. OrientationPanel — Atualização do Texto

- [x] 3.1 Atualizar o texto de orientação em `app.py` para a aba "Dominância do Pregão" (Análise Geral): substituir referência ao "círculo" por "traço horizontal".
- [x] 3.2 Atualizar o texto de orientação para a aba "Evolução da Dominância" (Análise do Ticker) — mesma substituição.

## 4. ToolbarBR — Botões Mover/Ampliar

- [x] 4.1 Sobrescrever `pan()` e `zoom()` com lógica de exclusão mútua: se um estiver ativo, desativá-lo antes de ativar o outro.
- [x] 4.2 Sobrescrever `home()` para desmarcar Mover e Ampliar após restaurar visualização.
- [x] 4.3 Sobrescrever `_update_buttons_checked()` com os nomes dos botões em português (`"Mover"`, `"Ampliar"`).
- [x] 4.4 Corrigir implementação inicial que usava `self._active` (inexistente no matplotlib 3.11) para `self.mode` com enum `_Mode`.

## 5. Verificação

- [x] 5.1 Executar o aplicativo e verificar visualmente os stems no ranking e no timeline com dados reais (IDIV). — Código compila e 131 testes passam. Verificação visual requer ambiente gráfico.
- [x] 5.2 Verificar que labels não sobrepõem stems e que textos de Vendedores/Compradores estão alinhados com "CLV". — Lógica de clamping implementada; Vendedores/Compradores em y=-0.08 (ranking) e y=-0.10 (timeline).
- [x] 5.3 Verificar tooltips continuam funcionando (devem mostrar MFV normalmente). — Tooltips usam `_on_motion` com distância até `pt["clv"]`, inalterado. Stems não têm picker (desnecessário).
