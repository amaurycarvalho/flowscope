## Why

Sem uma trava automatizada, o fluxo de dependências entre camadas volta a se degradar a cada nova feature. Hoje só existe verificação de fronteira para o subpacote FII, e as violações legadas de `presentation -> infrastructure` e de regras de domínio em `presentation` não são detectadas. Esta é a fundação do programa `clean-architecture-layering`: torna o contrato de fronteira verificável e reversível, criando o mecanismo que os incrementos seguintes vão encolher.

## What Changes

- Teste de fronteira generalizado para `domain`, `application`, `infrastructure` e `presentation`, cobrindo os imports proibidos definidos em `specs/layer-boundaries/spec.md` do change chapéu.
- Allowlist explícita das violações legadas (arquivo de dados versionado), que só pode encolher; import novo fora do permitido reprova o teste.
- Verificação de que a allowlist está vazia é o critério de fechamento do programa (change `enforce-clean-architecture-boundaries`).
- Documentação da convenção de view-model (aplicação devolve dados prontos; apresentação formata/desenha) como referência para os incrementos.
- **BREAKING (interno)**: a partir daqui, violações de fronteira novas reprovam o quality gate.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): é mudança de tooling/teste que implementa o contrato já especificado pela capability `layer-boundaries` do change `clean-architecture-layering`, sem alterar comportamento observável do produto.

## Impact

- **Depende de**: contrato definido em `openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`.
- **Código afetado**: `tests/test_domain/test_fii/test_layer_boundaries.py` (generalizado/reaproveitado) e um novo teste + arquivo de allowlist.
- **Sem impacto no binário do produto**: nenhuma mudança em `src/flowscope`.
- **Habilita**: todos os increments filhos, que removem entradas da allowlist ao mover código e testes.
