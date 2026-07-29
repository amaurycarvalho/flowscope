## Why

O RFC-002 define a extração de Informes Mensais Estruturados (type=40) — relatórios com composição de carteira, resultados financeiros e indicadores de performance. O modelo de dados é mais rico que o de proventos, exigindo entidades próprias e parsing multi-tabela. Esta change implementa o informe mensal sobre a infraestrutura de `structured-earnings` (B3FundosClient, CacheManager, parsing HTML base), de forma ticker-agnóstica: qualquer ticker pode ser consultado, com dados retornados apenas quando disponíveis.

## What Changes

- Novas entidades em `domain/structured/`: `CarteiraAtivo`, `Carteira`, `Resultados`, `Indicadores`, `OutrasInformacoes`, `InformeMensal`
- Value object `Percentual` para valores percentuais
- Protocolo `InformeMensalRepository` separado de `ProventosRepository`
- Use case `ExtrairInformeMensalUseCase` orquestrando resolução → listagem (type=40) → extração multi-tabela
- Classificação de múltiplas tabelas por contexto (carteira, resultados, indicadores, outras info)
- Validação cruzada de totais como warning
- `InformeMensal.to_text()` como precursor para VectorStore no `llm-chat`
- CLI: `--informe-mensal`

## Capabilities

### New Capabilities

- `informe-mensal-domain`: Entidades — `CarteiraAtivo`, `Carteira`, `Resultados`, `Indicadores`, `OutrasInformacoes`, `InformeMensal` — e value object `Percentual`; `to_text()` para VectorStore
- `informe-mensal-extraction`: Pipeline type=40 — listagem, extração multi-tabela com classificação de contexto, validação cruzada de totais, use case

### Modified Capabilities

- `cli-interface`: Novo argumento `--informe-mensal`

## Impact

- **Dependência**: Requer `structured-earnings` implementada
- **Código**: Extensão de `domain/structured/entities.py`, `application/structured_ports.py`, `application/structured_use_cases.py`, `infrastructure/b3/structured_parser.py`, `infrastructure/b3/structured_repository.py`, `presentation/cli.py`
- **Cache**: Chaves `fund_docs_{idFNET}_40_{inicio}_{fim}` e `fund_detail_{idDocumento}`
