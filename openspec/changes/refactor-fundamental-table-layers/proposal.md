## Why

A fatia de Fundamentos concentra regras puras na apresentação: a montagem das
linhas da tabela e do CSV (`presentation/gui/charts/fundamental_rows.py`), a
formatação de exibição (`fundamental_formatters.py`) e a amostragem/construção
das séries da evolução (`fundamental_evolution_data.py`). O controlador
fundamentalista (`presentation/gui/controller_fundamental.py`) importa
`infrastructure` para construir o adaptador de preço de mercado. Como
consequência, boa parte dos 91 testes de `test_fundamental_table.py` e os 16 de
`test_fundamental_evolution_data.py` ficam na apresentação, e a apresentação
recalcula view-models a partir de estruturas de domínio. Esta fatia move a
montagem de linhas/CSV e a evolução para `application` (view-models prontos),
injeta o adaptador de mercado pelo composition root e remove a entrada de
`controller_fundamental` da allowlist.

## What Changes

- `montar_linhas`, `montar_csv`, o layout de colunas e os formatadores de
  exibição saem de `presentation/gui/charts/fundamental_rows.py` e
  `fundamental_formatters.py` para `application/fundamental/`, como view-models
  prontos; a apresentação apenas insere nas `Treeview` e copia o texto.
- A amostragem Fibonacci e a montagem das séries de evolução
  (`fundamental_evolution_data.py`) saem de `presentation` para `application`.
- `app_csv.py` passa a montar o CSV da tabela a partir do view-model de
  `application`.
- `controller_fundamental.py` recebe o adaptador de mercado (preço a partir do
  resultado diário) por injeção do composition root, deixando de importar
  `infrastructure`.
- Remoção da entrada `presentation/gui/controller_fundamental.py -> infrastructure`
  de `tests/architecture/allowlist.txt`.
- Migração dos testes puros (linhas, CSV, formatação e evolução) para
  `tests/test_application`; o painel mantém apenas wiring, estado e thread.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração que preserva o
comportamento observável, implementando o contrato `layer-boundaries` do change
`clean-architecture-layering`.

## Impact

- **Depende de**: `add-layer-architecture-guardrails` (allowlist e teste de
  fronteira) e `refactor-documentos-layers`/`refactor-noticias-layers` (padrão de
  injeção e composition root já estabelecidos).
- **Código movido**: `presentation/gui/charts/fundamental_rows.py`,
  `fundamental_formatters.py`, `fundamental_evolution_data.py`;
  `presentation/gui/controller_fundamental.py`; `presentation/gui/app_csv.py`.
- **Novos tipos**: `application/fundamental/*` (view-models de linha, CSV e
  séries de evolução).
- **Testes migrados**: os 16 testes de `test_fundamental_evolution_data.py` e a
  parcela pura de `test_fundamental_table.py` (montagem de linhas, CSV e
  formatação) para `tests/test_application`; o painel fica com o subconjunto de
  `needs_display` (estado/congelamento/rolagem/seleção).
- **Sem alteração de comportamento**: valores, rótulos, colunas, alinhamentos e
  ordem das séries permanecem idênticos.
