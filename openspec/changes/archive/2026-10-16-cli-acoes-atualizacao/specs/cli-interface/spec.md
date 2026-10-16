## ADDED Requirements

### Requirement: Leitura da data de referência via CLI

O sistema DEVE aceitar o subcomando `flowscope nav data-referencia` para imprimir, como JSON estruturado em `stdout`, a data de referência resolvida da última carga de fundamentos. O subcomando NÃO DEVE exigir caminho nem argumentos e DEVE reusar o mesmo núcleo de navegação das demais operações `nav`.

#### Scenario: Leitura da data de referência

- **WHEN** o usuário executa `flowscope nav data-referencia`
- **THEN** a data de referência resolvida DEVE ser impressa como JSON em `stdout`

#### Scenario: Sem data disponível

- **WHEN** não há marcador de última carga nem `last_date` no `config.json`
- **THEN** o comando DEVE indicar a ausência de data em JSON, sem erro fatal
