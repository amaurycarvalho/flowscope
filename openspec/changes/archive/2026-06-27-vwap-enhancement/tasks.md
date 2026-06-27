## 1. Domain: Alterar peso do VWAP

- [x] 1.1 Modificar `calculate_vwap()` em `domain/indicators.py` para usar `fin_instr_qty` como peso no lugar de `fin_vol`
- [x] 1.2 Atualizar testes em `test_domain/test_indicators.py` com valores esperados do novo cálculo

## 2. Application: Expor dados diários no use case

- [x] 2.1 Modificar `AnalyzeTickersUseCase.execute()` para incluir chave `daily_data` no resultado de cada ticker, com lista de dicts contendo `date`, `avg_price`, `min_price`, `max_price`, `last_price`, `fin_instr_qty`
- [x] 2.2 Adicionar campo `total_fin_instr_qty` no resultado do VWAP (dentro do dict `vwap`) e atualizar `scatter.py` que usava `total_fin_vol`

## 3. Presentation: Novo gráfico VWAP (violin plot + errorbar + scatter)

- [x] 3.1 Reescrever `VWAPHistChart` em `presentation/gui/charts/vwap_hist.py`: implementar violin plot horizontal com perfil de volume usando `fill_between`, onde a largura em cada bucket de preço é proporcional à soma de FinInstrmQty
- [x] 3.2 Adicionar errorbar ao gráfico: VWAP geral como centro, menor MinPric como erro inferior, maior MaxPric como erro superior (`ax.errorbar`)
- [x] 3.3 Adicionar scatter plot ao gráfico: LastPric da data mais recente para cada ticker (`ax.scatter`)
- [x] 3.4 Ajustar extração de dados do `daily_data` no método `update()` da nova chart class

## 4. Presentation: Atualizar UI

- [x] 4.1 Substituir tooltip do Radiobutton VWAP em `app.py` pelo texto: "Preço médio ponderado pela quantidade de ativos negociados. Mostra distribuição de preços no período."
- [x] 4.2 Atualizar título do gráfico VWAP de `"VWAP Histogram"` para `"VWAP — Distribuição de Preços"` em `app.py`

## 5. Verificação

- [x] 5.1 Executar suite de testes (`pytest tests/`) e garantir que todos passam
- [x] 5.2 Verificar que o gráfico VWAP carrega e exibe corretamente para dados reais (requer execução manual da GUI)
