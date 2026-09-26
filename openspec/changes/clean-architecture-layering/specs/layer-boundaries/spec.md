## Purpose

Define o contrato de fronteira entre as camadas do FlowScope, garantindo o fluxo de dependências do Clean Architecture, a localização correta de entidades e regras de domínio, e um orçamento de testes de UI restrito ao estritamente necessário.

## ADDED Requirements

### Requirement: Fluxo de dependências entre camadas

O código DEVE respeitar o fluxo unidirecional `presentation -> application -> domain`, com `infrastructure` dependendo apenas de `application` e `domain`, e `domain` sem dependências das demais camadas.

#### Scenario: Domínio isolado

- **WHEN** qualquer módulo sob `src/flowscope/domain` é analisado
- **THEN** ele NÃO DEVE importar `flowscope.application`, `flowscope.infrastructure` nem `flowscope.presentation`

#### Scenario: Aplicação isolada das camadas externas

- **WHEN** qualquer módulo sob `src/flowscope/application` é analisado
- **THEN** ele NÃO DEVE importar `flowscope.infrastructure` nem `flowscope.presentation`

#### Scenario: Apresentação fala apenas com a aplicação

- **WHEN** qualquer módulo sob `src/flowscope/presentation` é analisado, exceto os pontos de composição explicitamente listados na allowlist
- **THEN** ele NÃO DEVE importar `flowscope.infrastructure`

### Requirement: Localização de entidades e regras de domínio

Entidades, objetos de valor e regras de negócio DEVEM residir em `domain` ou `application`; `infrastructure` DEVE conter apenas I/O, integração, parsing e cache, e `presentation` DEVE conter apenas formatação e desenho.

#### Scenario: Entidade de catálogo em domínio

- **WHEN** uma entidade que representa documento, notícia ou agrupamento de catálogo é procurada no código-fonte
- **THEN** ela DEVE estar declarada em `flowscope.domain`, e não em `flowscope.infrastructure`

#### Scenario: Regra de classificação fora da apresentação

- **WHEN** uma função que decide uma categoria de domínio (por exemplo quadrante, tipo de notícia ou classificação de pregão) é procurada
- **THEN** ela NÃO DEVE residir sob `flowscope.presentation`

### Requirement: Fronteira de view-model

Painéis DEVEM consumir dados já preparados pela aplicação (view-models) e NÃO DEVEM recalcular regras de negócio a partir de estruturas brutas.

#### Scenario: Painel recebe view-model

- **WHEN** um painel de gráfico é renderizado
- **THEN** os dados de entrada DEVEM ser estruturas já prontas retornadas por caso de uso ou read-model da aplicação
- **AND** a apresentação NÃO DEVE acessar indicadores brutos para reclassificar ou reinterpretar domínio

### Requirement: Guardrail de fronteira com allowlist decrescente

DEVE existir um teste automatizado que verifica as fronteiras de importação de todas as camadas, com uma allowlist explícita das violações legadas; a allowlist DEVE apenas encolher e DEVE estar vazia ao final do programa.

#### Scenario: Violação nova reprova

- **WHEN** um import entre camadas fora do permitido é introduzido sem constar na allowlist
- **THEN** o teste de fronteira DEVE falhar

#### Scenario: Allowlist só encolhe

- **WHEN** um incremento remove uma violação legada
- **THEN** a entrada correspondente DEVE ser removida da allowlist
- **AND** o teste de fronteira DEVE permanecer verde

#### Scenario: Fechamento zera a allowlist

- **WHEN** o incremento de fechamento é concluído
- **THEN** a allowlist DEVE estar vazia

### Requirement: Orçamento de testes de UI

Testes de apresentação DEVEM verificar apenas wiring, estado de widget/botão, empty-state e ciclo de thread/queue; lógica pura DEVE ser testada nas camadas `domain` e `application`, sem exigir interface gráfica.

#### Scenario: Lógica pura testada sem display

- **WHEN** um teste cobre classificação, agregação ou geração de resumo de domínio
- **THEN** ele DEVE residir em `tests/test_domain` ou `tests/test_application`
- **AND** NÃO DEVE exigir a variável de ambiente `DISPLAY`

#### Scenario: Teste de UI limitado ao essencial

- **WHEN** um teste exige interface gráfica
- **THEN** ele DEVE verificar um comportamento que só existe na camada de apresentação (wiring, estado visual, empty-state ou thread/queue)

### Requirement: Paridade de comportamento

A reorganização DEVE preservar a saída observável do produto: rótulos, textos, números e ordem de exibição permanecem idênticos antes e depois de cada incremento.

#### Scenario: Saída preservada

- **WHEN** os mesmos dados de entrada são processados antes e depois de um incremento
- **THEN** os valores e textos exibidos DEVEM ser idênticos
