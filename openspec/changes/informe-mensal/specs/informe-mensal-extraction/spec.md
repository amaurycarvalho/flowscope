## ADDED Requirements

### Requirement: Protocolo InformeMensalRepository
O sistema DEVE definir `InformeMensalRepository` com `resolver_ticker(ticker) -> str | None`, `listar_documentos(id_fnet, data_inicio, data_fim, tipo) -> list[dict]` e `extrair_informe_mensal(id_documento) -> InformeMensal`.

### Requirement: Listagem de documentos type=40
O sistema DEVE listar documentos com `type=40`, reutilizando paginação e cache do `B3FundosClient`. Se resolução retornar `None`, retornar lista vazia.

#### Scenario: Ticker sem idFNET — retorna vazio
- **WHEN** `listar_documentos` é chamado com id_fnet=None
- **THEN** o sistema DEVE retornar lista vazia sem erro

### Requirement: Parsing multi-tabela com classificação de contexto
O sistema DEVE extrair e classificar tabelas do HTML: `"carteira"`, `"resultados"`, `"indicadores"`, `"outras_informacoes"`, fallback `"geral"`.

#### Scenario: Tabelas classificadas corretamente
- **WHEN** o HTML contém 4 tabelas com headings distintos
- **THEN** cada tabela DEVE ser classificada no contexto correto

### Requirement: Validação cruzada de totais
O sistema DEVE validar `carteira.total_ativos` contra soma dos `valor_mercado` e `resultados.resultado_liquido` contra receitas - despesas. Divergências DEVEM ser logadas como warning.

### Requirement: Pipeline via ExtrairInformeMensalUseCase
O sistema DEVE expor `ExtrairInformeMensalUseCase` que retorna `list[InformeMensal]`, com `progress_callback` e tratamento de erro por documento.

#### Scenario: Ticker sem dados
- **WHEN** use case executado com ticker `PETR4`
- **THEN** retornar lista vazia sem erro

### Requirement: CLI para informe mensal
O sistema DEVE expor `--informe-mensal <TICKER>` com `--data-inicio`, `--data-fim` e `--output`.
