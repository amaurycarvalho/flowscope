## 1. Aplicação — read-model de rede

- [x] 1.1 Criar `application/network/dados.py` com `DadosRede`, `extrair_series`, as mensagens (`MENSAGEM_SEM_TICKERS`, `MENSAGEM_POUCAS_OBS`, `AVISO_COINT_INDISPONIVEL`) e os formatadores/rótulos (`formatar_correlacao`, `formatar_half_life`, `formatar_modularidade`, `rotulo_diagnostico`, `mensagem_indisponivel`) movidos de `presentation/gui/charts/network_data.py`; verificar com testes puros de extração de séries e rótulos
- [x] 1.2 Atualizar `correlation_network_panel.py` para consumir `application.network.dados` e remover `presentation/gui/charts/network_data.py`; verificar o painel com fakes e paridade de séries

## 2. Testes e verificação

- [x] 2.1 Migrar os testes puros de `tests/test_presentation/test_network_data.py` para `tests/test_application/test_network_data.py` e ajustar o import de `AVISO_COINT_INDISPONIVEL` nos testes de painel/integração; verificar ausência de `DISPLAY` nos testes puros
- [x] 2.2 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento, incluindo o guardrail de fronteira
