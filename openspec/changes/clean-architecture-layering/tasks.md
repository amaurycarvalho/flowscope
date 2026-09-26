# Tasks — clean-architecture-layering (change chapéu)

Esta change coordena. Cada tarefa cria um change filho com seus próprios artefatos
de planejamento (`proposal`, `design` e `tasks`; `specs` quando houver mudança de
comportamento, ou `skip_specs: true` em refactor/tooling); nenhuma tarefa
implementa código aqui. Verificação de cada criação: `openspec validate <name>`
passa e o change aparece em `openspec list`.

## 1. Fundação (transversal)

- [x] 1.1 Criar o change `add-layer-architecture-guardrails` (teste de fronteira generalizado para todas as camadas, allowlist inicial de violações legadas e convenção de view-model) e verificar com `openspec validate add-layer-architecture-guardrails`
- [x] 1.2 Confirmar que o change filho 1.1 referencia o contrato `layer-boundaries` deste chapéu (via `skip_specs: true`, por ser tooling sem mudança de comportamento); verificar em `openspec show add-layer-architecture-guardrails`

## 2. Fatias de maior payoff de teste

- [x] 2.1 Criar o change `refactor-documentos-layers` (entidades de catálogo para `domain`; catálogo/resumo em `application`; painéis só desenham) e verificar com `openspec validate refactor-documentos-layers`
- [x] 2.2 Criar o change `refactor-noticias-layers` (classificação e entidades de notícia para `domain`/`application`; painel só desenha) e verificar com `openspec validate refactor-noticias-layers`
- [x] 2.3 Criar o change `refactor-fundamental-table-layers` (linhas, CSV e evolução dos fundamentos como view-models de `application`) e verificar com `openspec validate refactor-fundamental-table-layers`

## 3. Fatias de gráficos e indicadores

- [x] 3.1 Criar o change `refactor-correlation-network-layers` (extração de séries para `application`) e verificar com `openspec validate refactor-correlation-network-layers`
- [x] 3.2 Criar o change `refactor-dominance-panels-layers` (construção de ranking/timeline para `application`) e verificar com `openspec validate refactor-dominance-panels-layers`
- [x] 3.3 Criar o change `refactor-quadrant-vwap-layers` (quadrante para `domain`; dados de VWAP para `application`) e verificar com `openspec validate refactor-quadrant-vwap-layers`
- [x] 3.4 Criar o change `refactor-price-range-layers` (classificação de pregão para `domain`; normalização e dimensionamento permanecem em `presentation`) e verificar com `openspec validate refactor-price-range-layers`
- [x] 3.5 Criar o change `refactor-flow-panels-layers` (extração de métricas e resumo do fluxo para `application`/`domain`) e verificar com `openspec validate refactor-flow-panels-layers`

## 4. Integração com o chat

- [x] 4.1 Criar o change `refactor-chat-context-layers` (montagem de contexto como `application`, painel só exibe) e verificar com `openspec validate refactor-chat-context-layers`

## 5. Fechamento para o estado-alvo (A)

- [ ] 5.1 Criar o change `enforce-clean-architecture-boundaries` (allowlist zerada; imports de `infrastructure` restritos ao composition root) e verificar com `openspec validate enforce-clean-architecture-boundaries`
- [ ] 5.2 Verificar a conclusão do programa: todos os changes filhos arquivados, allowlist de fronteira vazia e guardrail verde, com `make test` e `make complexity`
