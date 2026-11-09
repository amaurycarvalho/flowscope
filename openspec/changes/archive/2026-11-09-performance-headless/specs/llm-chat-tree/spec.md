# Spec Delta

## ADDED Requirements

### Requirement: Ramo `/performance` da árvore de conhecimento

O sistema DEVE expor o ramo `/performance` na árvore de conhecimento quando houver snapshot local válido, com `configuracao`, `benchmarks/<benchmark>/resumo` e `benchmarks/<benchmark>/tickers/<ticker>`. O ramo DEVE ser montado somente do snapshot, sem recalcular, baixar ou consultar B3/CVM. Snapshot ausente ou inválido DEVE omitir o ramo; snapshot sem resultados DEVE expor a configuração e uma orientação de estado vazio.

#### Scenario: Navegação do ramo

- **WHEN** a LLM lista `/performance` e existe snapshot
- **THEN** a árvore DEVE devolver a configuração e os benchmarks disponíveis como nós navegáveis

#### Scenario: Leitura de um ticker

- **WHEN** a LLM obtém `/performance/benchmarks/IFIX/tickers/<ticker>`
- **THEN** o conteúdo DEVE trazer retorno do ticker, retorno do índice, excesso em pontos percentuais, número de observações e aviso de evento suspeito quando aplicável

#### Scenario: Resumo do benchmark

- **WHEN** a LLM obtém `/performance/benchmarks/<benchmark>/resumo`
- **THEN** o conteúdo DEVE informar a disponibilidade do índice, a base de retorno e os tickers elegíveis

#### Scenario: Snapshot ausente

- **WHEN** não existe snapshot local de Performance
- **THEN** o ramo `/performance` NÃO DEVE existir e os demais ramos DEVEM permanecer navegáveis

#### Scenario: Snapshot inválido

- **WHEN** o snapshot está corrompido ou tem schema divergente
- **THEN** o ramo `/performance` NÃO DEVE existir, o problema DEVE ser registrado e a árvore NÃO DEVE falhar

#### Scenario: Snapshot sem resultados

- **WHEN** o snapshot existe, mas não há benchmark ou ticker elegível
- **THEN** o ramo DEVE expor `/performance/configuracao` e uma folha de orientação com o motivo, sem barras ou resultados inventados

#### Scenario: Sem efeitos colaterais

- **WHEN** o chat navega o ramo `/performance`
- **THEN** nenhum cálculo, download, extração ou consulta externa DEVE ocorrer

### Requirement: Manifesto anuncia os caminhos de Performance

O manifesto DEVE anunciar `/performance` e seus caminhos canônicos apenas quando o ramo existir, incluindo uma linha no playbook para perguntas de desempenho relativo ao índice. O conteúdo pesado e os resultados por ticker NÃO DEVEM integrar o manifesto; configuração e resumo DEVEM ser obtidos por navegação, respeitando o teto de tokens.

#### Scenario: Ramo presente é anunciado

- **WHEN** o snapshot existe e o ramo `/performance` está na árvore
- **THEN** o mapa e a descrição DEVEM anunciar `/performance/configuracao` e `/performance/benchmarks/<benchmark>/{resumo,tickers/<ticker>}`

#### Scenario: Ramo ausente não é anunciado

- **WHEN** não há snapshot ou o ramo foi omitido
- **THEN** o manifesto NÃO DEVE citar caminhos de `/performance`

#### Scenario: Playbook de desempenho

- **WHEN** o ramo `/performance` existe
- **THEN** o playbook DEVE orientar a navegar `/performance/benchmarks/<benchmark>/resumo` e as folhas de ticker para responder sobre desempenho relativo ao índice

#### Scenario: Metadados não pré-injetam resultados

- **WHEN** o manifesto é montado com o ramo `/performance`
- **THEN** os resultados por ticker NÃO DEVEM integrar a seção de metadados e o teto de tokens DEVE ser respeitado

#### Scenario: Contexto do cálculo anunciado

- **WHEN** a LLM navega o ramo
- **THEN** o período, a amostragem e a data de referência DEVEM estar disponíveis em `/performance/configuracao` e no resumo do benchmark
