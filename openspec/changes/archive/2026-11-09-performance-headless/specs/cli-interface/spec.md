# Spec Delta

## ADDED Requirements

### Requirement: Exportação da Performance via `exportar performance`

O sistema DEVE aceitar `flowscope exportar performance --formato <csv|json> [--benchmark <IFIX|IBOV|IDIV>] [--saida <ARQUIVO>]` e exportar somente o snapshot local mais recente, sem recalcular nem consultar a rede. O CSV DEVE usar `;` e incluir o contexto do cálculo e os dados por ticker; o JSON DEVE conter o snapshot estruturado.

#### Scenario: Exportação CSV

- **WHEN** o usuário executa `flowscope exportar performance --formato csv` e existe snapshot
- **THEN** o conteúdo CSV DEVE ser impresso em `stdout`, com `;` e as colunas de contexto e de cada ticker

#### Scenario: Exportação JSON

- **WHEN** o usuário executa `flowscope exportar performance --formato json`
- **THEN** o snapshot estruturado DEVE ser impresso em `stdout`, sem gravar arquivo quando `--saida` for omitido

#### Scenario: Filtro por benchmark

- **WHEN** o usuário informa `--benchmark IFIX` e o snapshot contém IFIX
- **THEN** apenas os resultados desse benchmark DEVEM ser exportados

#### Scenario: Snapshot ausente

- **WHEN** não existe snapshot local de Performance
- **THEN** o comando DEVE devolver erro estruturado `performance_ausente` com dica para executar `flowscope atualizar performance` ou iniciar o MCP com `--data`, sem consultar a rede

#### Scenario: Benchmark sem resultado

- **WHEN** o usuário filtra um benchmark que não existe no snapshot
- **THEN** o comando DEVE devolver erro estruturado `benchmark_ausente` com a lista de benchmarks disponíveis

#### Scenario: Formato inválido

- **WHEN** o usuário informa formato diferente de `csv` ou `json`
- **THEN** o comando DEVE ser rejeitado com erro de argumentos, sem ler nem gravar arquivo

#### Scenario: Saída em arquivo

- **WHEN** o usuário adiciona `--saida performance.csv`
- **THEN** o conteúdo exportado DEVE ser gravado no caminho indicado, sem imprimir o conteúdo em `stdout`

#### Scenario: Falha de escrita

- **WHEN** o caminho de `--saida` não pode ser gravado
- **THEN** o comando DEVE falhar com erro estruturado e registrar `WARNING` com o caminho e a causa
