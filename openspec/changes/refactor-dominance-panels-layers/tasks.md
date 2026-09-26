## 1. Aplicação — view-models e geometria

- [ ] 1.1 Criar `application/dominance/ranking.py` com `RankingRow` e `build_rows`/`stem_lengths` movidos de `presentation/gui/charts/ranking_data.py`; verificar com testes puros de construção do ranking e dos comprimentos de haste
- [ ] 1.2 Criar `application/dominance/timeline.py` com `TimelineRow`, `build_rows` e `direction_balance` movidos de `presentation/gui/charts/timeline_data.py`; verificar com testes puros das linhas cronológicas e do balanço
- [ ] 1.3 Criar `application/dominance/hastes.py` com `stem_length`, `compute_stems` e `bar_colors` movidos de `presentation/gui/charts/dominance_data.py`; verificar com testes puros de geometria e cores

## 2. Apresentação — painéis só desenham

- [ ] 2.1 Atualizar `dominance_ranking.py` para consumir `application/dominance` e manter apenas `draw_ticker_labels` em `ranking_data.py`; verificar o painel com fakes e paridade de ordenação/rotulagem
- [ ] 2.2 Atualizar `dominance_timeline.py` para consumir `application/dominance`, manter `draw_stems`/hit-testing em `dominance_data.py` e remover `timeline_data.py`; verificar o painel com fakes e paridade de percentuais/tooltips

## 3. Testes e verificação

- [ ] 3.1 Criar `tests/test_application/test_dominance_data.py` com testes puros das funções movidas, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções
- [ ] 3.2 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
