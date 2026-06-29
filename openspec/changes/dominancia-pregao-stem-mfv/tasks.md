## 1. DominanceRankingChart — Stem e Ajustes

- [ ] 1.1 Substituir o scatter do círculo por `ax.hlines` desenhando o stem de x=0 até `clv + stem_len`, com `stem_len = √(|mfv|/max_mfv) × 0.10` (mín. 0.015). Manter supressão para `mfv == 0.0` ou `|clv| < 0.05`.
- [ ] 1.2 Atualizar posição do label do ticker: calcular `label_x = clv + stem_len + 0.02` (positivo) ou `clv - stem_len - 0.02` (negativo). Se ultrapassar xlim, usar `xlim - 0.02`.
- [ ] 1.3 Mover textos "Compradores →" e "← Vendedores" de `y=-0.02` para `y=-0.08` (transAxes).

## 2. DominanceTimelineChart — Stem e Ajustes

- [ ] 2.1 Substituir o scatter do círculo por stem horizontal usando a mesma lógica, porém com `stem_max_data = 0.15` (timeline tem mais espaço horizontal).
- [ ] 2.2 Ajustar posição dos labels de data conforme o stem (similar ao passo 1.2).
- [ ] 2.3 Mover textos "Compradores →" e "← Vendedores" de `y=-0.06` para `y=-0.10` (transAxes).

## 3. OrientationPanel — Atualização do Texto

- [ ] 3.1 Atualizar o texto de orientação em `app.py` para a aba "Dominância do Pregão" (Análise Geral): substituir referência ao "círculo" por "traço horizontal".
- [ ] 3.2 Atualizar o texto de orientação para a aba "Evolução da Dominância" (Análise do Ticker) — mesma substituição.

## 4. Verificação

- [ ] 4.1 Executar o aplicativo e verificar visualmente os stems no ranking e no timeline com dados reais (IDIV).
- [ ] 4.2 Verificar que labels não sobrepõem stems e que textos de Vendedores/Compradores estão alinhados com "CLV".
- [ ] 4.3 Verificar tooltips continuam funcionando (devem mostrar MFV normalmente).
