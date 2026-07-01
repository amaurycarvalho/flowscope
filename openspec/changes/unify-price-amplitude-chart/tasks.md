## 1. Refatorar GridSpec e estrutura do PriceRangePanel

- [ ] 1.1 Reduzir GridSpec de 4 rows para 2 rows (height_ratios=[3, 0.5]), manter hspace
- [ ] 1.2 Remover `self._ax_range_history`, `self._ax_efficiency` da inicialização
- [ ] 1.3 Renomear `self._ax_timeline` para `self._ax_main` (opcional, mas consistente)
- [ ] 1.4 Atualizar `update()` para não chamar `_build_range_history` nem `_build_efficiency_gauge`
- [ ] 1.5 Ajustar chamada a `tight_layout()` e `draw()`

## 2. Implementar plotagem unificada no axes principal

- [ ] 2.1 Criar método `_build_main_chart()` que substitui `_build_timeline()`, `_build_range_history()` e `_build_efficiency_gauge()`
- [ ] 2.2 Para cada row: desenhar barra de fundo (`barh`) representando a Eficiência (comprimento = eff, cor por threshold vermelho/amarelo/verde, alpha ~0.3)
- [ ] 2.3 Para cada row: desenhar a linha cinza do range normalizado (como hoje)
- [ ] 2.4 Para cada row: plotar marcadores (● close, M median, T typical, V VWAP, W weighted close) com posicionamento existente
- [ ] 2.5 Mapear Range % de cada dia para tamanho do ● (scatter marker size), usando escala linear entre min_s=40 e max_s=200, com clamping nos percentis 5-95

## 3. Atualizar tooltip e hover

- [ ] 3.1 Adicionar campo `amplitude_relativa` ao `_hover_data` para cada dia
- [ ] 3.2 Incluir "Ampl. Relativa: X.XX%" na tooltip (`_show_tooltip`)
- [ ] 3.3 Verificar que o hover funciona corretamente no axes unificado (event.inaxes)

## 4. Manter CLV gauge

- [ ] 4.1 Manter `_ax_clv` e `_build_clv_gauge()` no segundo slot do GridSpec
- [ ] 4.2 Verificar que o CLV continua mostrando o valor do último pregão

## 5. Atualizar nomenclatura e títulos

- [ ] 5.1 Alterar título do axes principal de "Price Range Timeline" para "Trajetória no Range"
- [ ] 5.2 Remover título "Range % Histórico" (não há mais subplot)
- [ ] 5.3 Remover título "Eficiência Diária" (agora é barra de fundo)
- [ ] 5.4 Manter título "CLV" no gauge

## 6. Atualizar texto de orientação

- [ ] 6.1 Em `app.py`, substituir o help text de "Amplitude de Preço" para refletir:
  - Três perguntas respondidas (onde / quanto / se andou com convicção)
  - Nomenclatura: Trajetória no Range, Amplitude Relativa, Eficiência Diária
  - Descrição das camadas visuais (barra de eficiência como fundo, ● tamanho = amplitude relativa)
  - Manutenção do CLV e classificação
- [ ] 6.2 Remover referências ao "Range % Histórico" como sub-gráfico

## 7. Verificar integração

- [ ] 7.1 Testar com dados reais (carregar B3, navegar para Amplitude de Preço, trocar tickers)
- [ ] 7.2 Verificar tooltip, setas, classificação e CLV
- [ ] 7.3 Verificar que o gráfico redimensiona corretamente
