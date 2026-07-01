## 1. Refatorar GridSpec e estrutura do PriceRangePanel

- [x] 1.1 Reduzir GridSpec de 4 rows para 2 rows (height_ratios=[3, 0.6]), manter hspace
- [x] 1.2 Remover `self._ax_range_history`, `self._ax_efficiency` da inicialização
- [x] 1.3 Renomear `self._ax_timeline` para `self._ax_main` (opcional, mas consistente)
- [x] 1.4 Atualizar `update()` para não chamar `_build_range_history` nem `_build_efficiency_gauge`
- [x] 1.5 Ajustar chamada a `tight_layout()` e `draw()`

## 2. Implementar plotagem unificada no axes principal

- [x] 2.1 Criar método `_build_main_chart()` que substitui `_build_timeline()`, `_build_range_history()` e `_build_efficiency_gauge()`
- [x] 2.2 Para cada row: desenhar barra de fundo (`barh`) representando a Eficiência (comprimento = eff, cor por threshold vermelho/amarelo/verde, alpha ~0.3)
- [x] 2.3 Para cada row: desenhar a linha cinza do range normalizado (como hoje)
- [x] 2.4 Para cada row: plotar marcadores (● close, M median, T typical, V VWAP, W weighted close) com posicionamento existente
- [x] 2.5 Mapear Range % de cada dia para tamanho do ● (scatter marker size), usando escala linear entre min_s=40 e max_s=200, com clamping nos percentis 5-95

## 3. Atualizar tooltip e hover

- [x] 3.1 Adicionar campo `amplitude_relativa` ao `_hover_data` para cada dia
- [x] 3.2 Incluir "Ampl. Relativa: X.XX%" na tooltip (`_show_tooltip`)
- [x] 3.3 Verificar que o hover funciona corretamente no axes unificado (event.inaxes)

## 4. Manter CLV gauge

- [x] 4.1 Manter `_ax_clv` e `_build_clv_gauge()` no segundo slot do GridSpec
- [x] 4.2 Verificar que o CLV continua mostrando o valor do último pregão
- [x] 4.3 Adicionar labels "← Vendedores" (vermelho) e "Compradores →" (verde) abaixo do gauge CLV
- [x] 4.4 Atualizar título do CLV de "CLV" para "CLV (data mais recente)"
- [x] 4.5 Reduzir altura do CLV: height_ratio de 0.8 para 0.6 (~20% menor)

## 5. Atualizar nomenclatura e títulos

- [x] 5.1 Alterar título do axes principal de "Price Range Timeline" para "Amplitude de Preço — {ticker}"
- [x] 5.2 Remover título "Range % Histórico" (não há mais subplot)
- [x] 5.3 Remover título "Eficiência Diária" (agora é barra de fundo)
- [x] 5.4 Manter título "CLV" no gauge (atualizado para "CLV (data mais recente)")

## 6. Ajustes no label de range diário

- [x] 6.1 Substituir label único "Min: X.XX  Max: X.XX" centralizado por dois labels separados
- [x] 6.2 Posicionar "Min: X.XX" abaixo do 0% (x=0 data coords)
- [x] 6.3 Posicionar "Max: X.XX" abaixo do 100% (x=1 data coords)
- [x] 6.4 Descer ambos ~1 altura da fonte (y=-0.08 axes coords)

## 7. Substituir setas por linhas na trajetória

- [x] 7.1 Remover `ax.arrow()` (que gerava artefatos visuais com `ec="gray"` e cabeça larga)
- [x] 7.2 Substituir por `ax.plot([x0, x1], [y0, y1])` com mesma cor, espessura e alpha
- [x] 7.3 Verificar que o traçado extra (linhas angulares fantasmas) desapareceu

## 8. Atualizar texto de orientação

- [x] 8.1 Em `app.py`, substituir o help text de "Amplitude de Preço" para refletir:
  - Três perguntas respondidas (onde / quanto / se andou com convicção)
  - Nomenclatura: Trajetória no Range, Amplitude Relativa, Eficiência Diária
  - Descrição das camadas visuais (barra de eficiência como fundo, ● tamanho = amplitude relativa)
  - Manutenção do CLV e classificação
- [x] 8.2 Remover referências ao "Range % Histórico" como sub-gráfico
- [x] 8.3 Adicionar significado interpretativo de cada classificação:
  - "Pregão Lateral": amplitude baixa + eficiência baixa → indecisão, mercado sem direção
  - "Volatilidade sem Direção": amplitude alta + eficiência baixa → nervosismo, barulho sem sinal
  - "Movimento Consistente": amplitude baixa + eficiência alta → foco direcional com pouca oscilação
  - "Movimento Direcional Forte": amplitude alta + eficiência alta → consenso forte no fluxo de ordens

## 9. Verificar integração

- [x] 9.1 Testar com dados reais (carregar B3, navegar para Amplitude de Preço, trocar tickers)
- [x] 9.2 Verificar tooltip, linhas de trajetória, classificação e CLV
- [x] 9.3 Verificar que o gráfico redimensiona corretamente
