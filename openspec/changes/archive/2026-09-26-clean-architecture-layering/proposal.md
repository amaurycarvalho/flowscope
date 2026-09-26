## Why

A camada de apresentação hoje concentra lógica de domínio e de aplicação (regras de classificação, agregação e narrativa em `presentation/gui/charts/*`) e importa `infrastructure` diretamente, enquanto entidades de domínio vivem em `infrastructure` (`document_catalog`, `noticias_catalogo`, `noticias_tipos`). Isso encarece os testes: `presentation` tem 773 testes (33% do total), 15 arquivos instanciam Tk real e ~263 testes exigem `DISPLAY` — ou seja, não rodam no CI headless. O objetivo é restaurar o fluxo de dependências do Clean Architecture e reduzir os testes de UI ao estritamente necessário, migrando a lógica pura para `domain`/`application` com testes rápidos e determinísticos.

## What Changes

Esta change é um **chapéu**: não implementa código nem altera comportamento. Ela fixa a arquitetura alvo, a convenção de fronteira e a ordem dos incrementos, e cria (em changes filhos) as refatorações.

- Define o contrato de fronteira entre camadas (`domain`, `application`, `infrastructure`, `presentation`) e a regra de importação de cada uma.
- Define a convenção de **view-model**: `application` devolve dataclasses prontas; `presentation` apenas formata e desenha.
- Estabelece um **guardrail** de fronteira com *allowlist* de violações legadas que só pode encolher, zerada no incremento de fechamento.
- Restringe o escopo dos testes de UI a wiring, estado de widget/botão, empty-state e ciclo de thread/queue; lógica pura passa a ser testada em `test_domain`/`test_application`.
- Coordena os incrementos filhos, na ordem: fundação de guardrails; Documentos; Notícias; Correlação/Rede; Dominância; Quadrante+VWAP; Amplitude de Preço; Fluxo Financeiro; Fundamentos; Chat; fechamento.
- **BREAKING (interno)**: imports entre camadas passam a ser validados por teste; violações novas reprovam o quality gate.

## Capabilities

### New Capabilities

- `layer-boundaries`: contrato arquitetural de dependências entre camadas, localização de entidades de domínio, convenção de view-models na fronteira, guardrail com allowlist decrescente e orçamento de testes de UI.

### Modified Capabilities

## Impact

- **Depende de**: `engineering-standards` (o guardrail entra no quality gate) e `presentation-test-coverage` (os increments filhos ajustam a cobertura ao mover testes).
- **Código afetado**: `src/flowscope/presentation/gui/charts/*_data.py` e `*_helpers.py`; entidades em `src/flowscope/infrastructure/document_catalog.py`, `noticias_catalogo.py`, `noticias_aquisicao.py`, `noticias_tipos.py`; imports `presentation -> infrastructure` (fora do composition root); `src/flowscope/application/*` (novos use cases/read-models/portas).
- **Testes afetados**: ~200-230 testes saem de `tests/test_presentation` para `tests/test_domain`/`tests/test_application`; os ~263 marcados `needs_display` caem para o conjunto mínimo de UI.
- **Sem alteração de comportamento do produto**: a saída exibida, os rótulos e os números permanecem idênticos; muda a localização do código e a estratégia de teste.
- **Rastreabilidade**: cada incremento filho terá seu próprio `proposal`/`specs`/`design`/`tasks`; esta change apenas os referencia e define a ordem.
