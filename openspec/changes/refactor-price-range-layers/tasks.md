## 1. Domínio — classificação de pregão

- [x] 1.1 Mover `classify_trend`, `classify_session` e `median_value` de `presentation/gui/charts/price_range_helpers.py` para `domain`, com `classify_session(last_date, range_pct_dict, eff_dict)`, e exportar no pacote de classificadores; verificar com testes puros das categorias e dos limites de 0,30

## 2. Apresentação — normalização e desenho

- [x] 2.1 Atualizar `price_range_helpers.py` para importar `classify_session` de `domain` e ajustar `draw_classification_text` (cálculo da última data), mantendo `normalize`/`size_mapper`/desenho na apresentação; verificar o painel com fakes e paridade da classificação/mediana

## 3. Testes e verificação

- [x] 3.1 Criar `tests/test_domain/test_session_classification.py` com testes puros de `classify_trend`, `median_value` e `classify_session`, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções
- [x] 3.2 Rodar `make test` e `make complexity` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
