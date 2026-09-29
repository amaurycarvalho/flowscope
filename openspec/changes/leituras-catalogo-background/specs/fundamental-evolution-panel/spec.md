## ADDED Requirements

### Requirement: Leitura do cache histórico fora da thread da interface

O sistema DEVE ler as observações do cache histórico e montar as séries da sub-aba "Evolução dos Fundamentos" fora da thread da interface, aplicando o resultado por evento na thread do Tk, com estado de carregamento durante a leitura. A origem continua sendo exclusivamente o cache histórico, sem aquisição de rede.

#### Scenario: Seleção com estado de carregamento
- **WHEN** o usuário seleciona a sub-aba "Evolução dos Fundamentos" com um ticker selecionado
- **THEN** a leitura do cache histórico DEVE ocorrer fora da thread da interface e as séries DEVEM ser aplicadas por evento ao concluir

#### Scenario: Interface responsiva durante a leitura
- **WHEN** a leitura do cache histórico está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Sem aquisição de rede
- **WHEN** as séries são montadas
- **THEN** nenhuma consulta a Fundamentus, B3, CVM ou outra fonte remota DEVE ser feita

#### Scenario: Leitura obsoleta descartada
- **WHEN** o ticker apresentado muda antes de uma leitura em andamento concluir
- **THEN** o resultado da leitura anterior NÃO DEVE ser aplicado ao novo ticker
