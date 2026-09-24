## Purpose

Permite indexar os documentos de um ticker no VectorStore a partir da linha de comando.

## ADDED Requirements

### Requirement: Indexação de documentos via CLI

O sistema DEVE aceitar `--index <TICKER>` para indexar documentos no VectorStore, com `--data-inicio` e `--data-fim` delimitando o período. Sem `[llm]` instalado, o comando DEVE exibir mensagem de instalação e encerrar com código 1.

#### Scenario: Indexação completa
- **WHEN** `flowscope --index ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29` é executado com `[llm]` instalado
- **THEN** os documentos das fontes disponíveis DEVEM ser indexados com mensagem de sucesso

#### Scenario: Dependências ausentes
- **WHEN** `flowscope --index ALZR11` é executado sem `[llm]` instalado
- **THEN** o sistema DEVE imprimir "Erro: flowscope[llm] não instalado" e encerrar com código 1
