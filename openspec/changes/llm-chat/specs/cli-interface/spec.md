## ADDED Requirements

### Requirement: Indexação de documentos via CLI
O sistema DEVE aceitar `--index <TICKER>` para indexar documentos no VectorStore, com `--data-inicio` e `--data-fim` obrigatórios. Usa fastembed como default.

#### Scenario: Indexação completa
- **WHEN** `flowscope --index ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29`
- **THEN** documentos das 3 fontes indexados com mensagem de sucesso

#### Scenario: Dependências ausentes
- **WHEN** `flowscope --index ALZR11` sem `[llm]` instalado
- **THEN** exibir "Erro: flowscope[llm] não instalado" e código 1
