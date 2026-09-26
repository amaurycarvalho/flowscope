## Context

Ver `proposal.md` — Why, e o contrato em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
Estado atual relevante:

- `presentation/gui/charts/network_data.py` já é puro (sem I/O): extrai as
  séries `(data, last_price)` de `_current_data` (`extrair_series`), reúne os
  tickers descartados (`DadosRede.sem_dados`) e deriva mensagens/rótulos de
  exibição (`MENSAGEM_SEM_TICKERS`, `MENSAGEM_POUCAS_OBS`,
  `AVISO_COINT_INDISPONIVEL`, `formatar_correlacao`, `formatar_half_life`,
  `formatar_modularidade`, `rotulo_diagnostico`, `mensagem_indisponivel`).
  Importa apenas `domain.network_analysis`.
- `presentation/gui/charts/correlation_network_panel.py` consome o read-model e
  chama `analyze_network` (domínio) e desenha o grafo force-directed; não importa
  `infrastructure` e não consta na allowlist.
- `domain/network_analysis.py` já concentra toda a regra (alinhamento,
  correlação, cointegração, comunidades, centralidade), com
  `MIN_OBS_CORR`/`MIN_OBS_COINT`.
- Testes: `test_network_data.py` (129 linhas, puro, sem `DISPLAY`),
  `test_correlation_network_panel.py` (249, UI), `test_correlation_network_integration.py`
  (220, wiring/UI + orientação).
- A allowlist de fronteira tem 3 entradas legadas sem relação com esta fatia
  (`app_about_actions`, `app_actions`, `llm/config_dialog`).

## Goals / Non-Goals

**Goals:**

- Colocar a extração de séries e o read-model de exibição em
  `application/network` como view-model pronto.
- Fazer `CorrelationNetworkPanel` depender de `application` e permanecer apenas
  com o desenho.
- Migrar os testes puros de `test_network_data.py` para `tests/test_application`.

**Non-Goals:**

- Não mover `analyze_network` nem o núcleo numérico de `domain`.
- Não mover o layout/drawing force-directed, a colorbar, a legenda ou a toolbar.
- Não alterar a allowlist (a fatia não tem violação `presentation -> infrastructure`).
- Não redesenhar mensagens, limiares (`MIN_OBS_CORR`/`MIN_OBS_COINT`) nem rótulos.

## Decisions

### D1 — Read-model de rede em `application/network`

`DadosRede`, `extrair_series`, as mensagens e os formatadores/rótulos migram de
`presentation/gui/charts/network_data.py` para `application/network/dados.py`. A
aplicação devolve as séries já normalizadas (`float`, ordenadas por data) e a
mensagem de estado vazio apropriada; a apresentação apenas desenha. Alternativa:
manter o read-model em `presentation` e mover só `extrair_series`. Rejeitada por
deixar a decisão de estado vazio e a interpretação de `daily_data` fora de
`application` e manter os testes puros na apresentação.

### D2 — Painel mantém a orquestração de análise

`CorrelationNetworkPanel.update` continua chamando `extrair_series` e
`analyze_network(dados.series)` e, em seguida, desenha. `analyze_network` já é
regra de domínio; esta fatia move apenas a extração de séries/read-model.
Alternativa: criar em `application` um read-model que devolva
`(DadosRede, NetworkResult)`. Rejeitada como escopo além do pedido
("extração de séries para `application`"), que misturaria a análise numérica com
a preparação do view-model.

### D3 — Migração direta sem reexportação

Como `network_data` só é consumido pelo painel e pelos próprios testes, o módulo
sai de `presentation` e os importadores passam a apontar para
`application.network.dados`; não há reexportação de compatibilidade. Alternativa:
manter um shim em `presentation`. Rejeitada por perpetuar código morto.

### D4 — Testes puros migram; painel fica com a UI

Os 129 testes de `test_network_data.py` vão para
`tests/test_application/test_network_data.py`, sem `DISPLAY`. Os testes de painel
e integração permanecem em `tests/test_presentation`, ajustando o import de
`AVISO_COINT_INDISPONIVEL` para `application`. Alternativa: manter os testes puros
na apresentação. Rejeitada por contrariar o orçamento de testes de UI do contrato.

## Risks / Trade-offs

- [Formatadores legados sem uso no painel] → `formatar_correlacao` e
  `formatar_half_life` não são chamados pelo painel, mas são cobertos por testes;
  mover junto (não remover) preserva a API e a paridade de comportamento.
- [Cobertura/mutation ao mover] → mover (não reescrever) os testes junto do
  código e rodar `make test`/`make quality-gate` ao final.
- [Import de `application` no painel] → é direção permitida
  (`presentation -> application -> domain`); o guardrail de fronteira confirma.

## Migration Plan

1. Criar `application/network/` com o read-model de séries, mensagens e rótulos.
2. Atualizar `correlation_network_panel.py` para consumir `application`.
3. Remover `presentation/gui/charts/network_data.py`.
4. Migrar os testes puros para `tests/test_application`; ajustar imports dos
   testes de painel/integração; rodar `make test` e `make quality-gate`.

Rollback: reverter o change restaura o módulo e o import; comportamento idêntico.

## Open Questions

- Nome do pacote (`application/network/` vs `application/correlation_network/`) e
  do módulo (`dados.py` vs `read_model.py`): decidir na implementação, sem
  impacto no contrato.
