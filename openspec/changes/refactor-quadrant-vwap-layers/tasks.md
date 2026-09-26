## 1. Domínio — classificação de quadrante

- [ ] 1.1 Mover `classify_quadrant` (e a constante dos quadrantes) de `presentation/gui/charts/quadrant_data.py` para `domain`, operando sobre `clv`/`vwap_dist`; verificar com testes puros de classificação (Q1–Q4 e pontos nos eixos)

## 2. Aplicação — quadrante e VWAP

- [ ] 2.1 Criar `application/quadrant` com `PontoQuadrante` e `build_trajectories`/`max_trajectory_qty`/`point_size`/`compute_scatter_data` movidos de `quadrant_data.py`; verificar com testes puros das trajetórias e da dispersão
- [ ] 2.2 Criar `application/quadrant` com `count_quadrants`/`pick_interpretation`/`generate_summary` movidos de `quadrant_data.py`; verificar com testes puros das contagens e dos textos do resumo
- [ ] 2.3 Criar `application/vwap` com `to_pct`/`collect_ticker_data`/`estimate_bucket_size`/`compute_violin_shapes` movidos de `vwap_data.py`; verificar com testes puros dos percentuais, buckets e formas

## 3. Apresentação — gráficos só desenham

- [ ] 3.1 Atualizar `quadrant_chart.py` para consumir `domain`/`application` e remover `quadrant_data.py`; verificar o gráfico com fakes e paridade de pontos/resumo
- [ ] 3.2 Atualizar `vwap_hist.py` para consumir `application` e remover `vwap_data.py`; verificar o gráfico com fakes e paridade de violinos/tooltips

## 4. Testes e verificação

- [ ] 4.1 Garantir os testes puros criados em `tests/test_domain/test_quadrant.py` e `tests/test_application/test_quadrant_data.py`/`test_vwap_data.py`, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções
- [ ] 4.2 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
