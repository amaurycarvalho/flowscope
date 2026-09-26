## 1. Domínio — normalização das pressões

- [x] 1.1 Criar `domain/strategies/pressure.py` com `pressure_percentages` movido de `presentation/gui/charts/financial_flow_helpers.py`; verificar com testes puros das proporções e do caso sem pressão

## 2. Aplicação — métricas e resumo

- [x] 2.1 Criar `application/flow/metrics.py` com o view-model `SessionFlowMetrics` e `build_session_metrics` movidos de `financial_flow_helpers.py`; verificar com testes puros da extração, dos nulos e dos derivados
- [x] 2.2 Criar `application/flow/summary.py` com `generate_summary` e os trechos `flow_intensity_part`/`close_position_part`/`dominance_part`/`conviction_part` movidos de `financial_flow_helpers.py`; verificar com testes puros dos ramos do resumo

## 3. Apresentação — painel só formata e desenha

- [x] 3.1 Atualizar `financial_flow_helpers.py` e `financial_flow_panel.py` para consumir `domain`/`application`, mantendo formatação, desenho e tooltip na apresentação; verificar o painel com fakes e paridade de métricas/resumo

## 4. Testes e verificação

- [x] 4.1 Criar `tests/test_application/test_flow_data.py` e `tests/test_domain/test_pressure.py` com testes puros das funções movidas, sem `DISPLAY`; verificar ausência de `DISPLAY` e cobertura das funções
- [x] 4.2 Rodar `make test` e `make complexity` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
