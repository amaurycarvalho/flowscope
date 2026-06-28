## Purpose

Define the DAG calculation engine that resolves indicator execution order based on declared dependencies, enabling automatic orchestration of indicator computation.

## Requirements

### Requirement: Motor de cálculo DAG

O sistema DEVE prover um motor de cálculo que resolva automaticamente a ordem de execução de indicadores com base em suas dependências declaradas, utilizando um grafo acíclico dirigido (DAG).

#### Scenario: Registro e execução de indicadores independentes

- **WHEN** dois indicadores sem dependências entre si são registrados no motor
- **THEN** o motor DEVE executar ambos em qualquer ordem e retornar os resultados de cada um

#### Scenario: Execução respeita ordem de dependências

- **WHEN** o indicador B depende do indicador A, e ambos são registrados no motor
- **THEN** o motor DEVE executar A antes de B e passar o resultado de A como entrada para B

#### Scenario: Detecção de dependência circular

- **WHEN** dois indicadores têm dependência circular (A depende de B e B depende de A)
- **THEN** o motor DEVE lançar uma exceção informando o ciclo

#### Scenario: Cache de resultados evita recomputação

- **WHEN** dois indicadores dependem do mesmo indicador A
- **THEN** o motor DEVE executar A apenas uma vez e reusar o resultado para ambos

### Requirement: Interface IndicatorStrategy

O sistema DEVE definir uma classe abstrata `IndicatorStrategy` que todo indicador concreto deve implementar, com metadados estáticos de identificação e dependências.

#### Scenario: Estratégia concreta é registrada no motor

- **WHEN** uma classe concreta que estende `IndicatorStrategy` com `id` e `dependencies` definidos é instanciada e registrada no motor
- **THEN** o motor DEVE reconhecer seu `id` e `dependencies` e incorporá-la ao grafo de execução

#### Scenario: Estratégia sem dependências é raiz do DAG

- **WHEN** um indicador declara `dependencies = []`
- **THEN** o motor DEVE tratá-lo como nó raiz, sem necessidade de entradas de outros indicadores

### Requirement: API pública do motor

O motor DEVE expor métodos `register()` para registrar estratégias e `execute(trades)` para executar todas as estratégias registradas e retornar um dicionário aninhado `{indicator_id: {ticker: resultado}}`.

#### Scenario: execute retorna todos os indicadores registrados

- **WHEN** 3 indicadores estão registrados e `execute()` é chamado com uma lista de TradeDay
- **THEN** o dicionário retornado DEVE conter exatamente 3 chaves, uma por indicador

#### Scenario: execute com lista vazia de trades

- **WHEN** `execute()` é chamado com `trades = []`
- **THEN** o motor DEVE retornar o dicionário com cada indicador contendo seu valor padrão (dict vazio ou equivalente)
