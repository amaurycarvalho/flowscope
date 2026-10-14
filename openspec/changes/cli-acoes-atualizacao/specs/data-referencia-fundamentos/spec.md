## Purpose

Registrar e expor, de forma somente-leitura, a data de referência usada na última carga de fundamentos, permitindo que um agendador externo e o Chat AI consultem qual fundamentos estão disponíveis no cache local.

## ADDED Requirements

### Requirement: Marcador da última carga de fundamentos

O sistema DEVE registrar, em `config.json`, um bloco `last_fundamentals` com a data de referência (`data`) e o instante da carga (`fetched_at`) sempre que uma carga de fundamentos for concluída — pela interface gráfica ou pela CLI. O marcador NÃO DEVE ser sobrescrito por uma sessão da GUI que apenas altere o campo de data sem carregar fundamentos.

#### Scenario: Carga pela CLI registra o marcador

- **WHEN** `flowscope atualizar fundamentos --data 2026-10-14` conclui
- **THEN** `config.json` DEVE conter `last_fundamentals.data = 2026-10-14` e um `fetched_at` correspondente

#### Scenario: Carga pela GUI registra o marcador

- **WHEN** a interface gráfica conclui uma carga de fundamentos para a data selecionada
- **THEN** `config.json` DEVE ser atualizado com `last_fundamentals` daquela data

### Requirement: Resolução da data de referência com fallback

O sistema DEVE resolver a data de referência consultada como o valor de `last_fundamentals.data` e, quando esse marcador estiver ausente, DEVE recorrer ao valor de `last_date` do `config.json`. A resolução DEVE ser o único ponto de verdade reusado pelas superfícies de leitura. Quando nenhum dos dois existir, a consulta DEVE indicar a ausência da data, sem erro.

#### Scenario: Marcador presente

- **WHEN** `last_fundamentals` existe no `config.json`
- **THEN** a data resolvida DEVE ser a de `last_fundamentals.data`

#### Scenario: Marcador ausente usa o fallback

- **WHEN** `last_fundamentals` não existe e `last_date` está presente
- **THEN** a data resolvida DEVE ser a de `last_date`

#### Scenario: Nenhuma data disponível

- **WHEN** nem `last_fundamentals` nem `last_date` existem
- **THEN** a consulta DEVE indicar a ausência de data, sem erro

### Requirement: Nó da data de referência na árvore de conhecimento

A árvore de conhecimento DEVE expor a data de referência como o nó `/fundamentos/data-referencia`, visível ao Chat AI, de modo que a informação seja navegável e pesquisável pelas operações existentes. O nó DEVE estar disponível tanto na composição headless (CLI e MCP) quanto na árvore do chat interno.

#### Scenario: Nó visível ao Chat AI

- **WHEN** a árvore de conhecimento é montada pela interface gráfica
- **THEN** o nó `/fundamentos/data-referencia` DEVE existir com a data resolvida como conteúdo

#### Scenario: Leitura pelas operações existentes

- **WHEN** o consumidor executa `obter` no caminho `/fundamentos/data-referencia`
- **THEN** a data de referência resolvida DEVE ser devolvida

### Requirement: Exposição da data de referência pela operação, tool e comando

O sistema DEVE expor a data de referência por uma operação canônica `data_referencia` no núcleo de navegação, pela tool MCP somente-leitura `nav_data_referencia` (sem argumentos) e pelo comando `flowscope nav data-referencia`. As três superfícies DEVEM devolver o mesmo valor resolvido.

#### Scenario: Operação canônica

- **WHEN** a operação `data_referencia` é executada no núcleo
- **THEN** a data de referência resolvida DEVE ser devolvida

#### Scenario: Tool MCP sem argumentos

- **WHEN** o cliente MCP invoca `nav_data_referencia` sem argumentos
- **THEN** a data de referência resolvida DEVE ser devolvida como conteúdo estruturado

#### Scenario: Comando CLI

- **WHEN** o usuário executa `flowscope nav data-referencia`
- **THEN** a data de referência resolvida DEVE ser impressa como JSON em `stdout`
