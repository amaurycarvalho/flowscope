## Why

O RFC-001 define a extração de rendimentos e amortizações de FIIs via API da B3, mas descreve uma implementação monolítica incompatível com a arquitetura Clean Architecture do FlowScope. Esta change adapta a funcionalidade ao estilo do projeto — entidades de domínio, ports/protocols, use cases, cache integrado e CLI — e a torna ticker-agnóstica: qualquer ticker pode ser consultado, com a fonte retornando dados apenas quando disponíveis (FIIs e outros fundos listados na B3).

## What Changes

- Novo módulo de domínio `domain/structured/` com entidades (`Entidade`, `Provento`, `DocumentoProvento`) e value objects (`CNPJ`, `ISIN`, `ValorProvento`)
- Uso do value object `Ticker` existente (genérico, sem validação de sufixo "11")
- Novo protocolo `ProventosRepository` em `application/structured_ports.py` desacoplando a camada de aplicação da API B3
- Novo use case `ExtrairProventosUseCase` orquestrando o fluxo: resolver ticker, listar documentos, extrair detalhes
- Extensão do `B3Client` com `B3FundosClient` para os endpoints `fundsListedProxy` (reutilizando padrões de token Base64, cache e progress callback)
- Resolução de ticker (ticker → idFNET) que retorna `None` graciosamente para tickers sem dados na API de fundos
- Novo `FundosRepository` em `infrastructure/b3/` implementando `ProventosRepository`
- Parsing flexível de HTML tabular via BeautifulSoup (nova dependência) com múltiplas estratégias de extração
- Integração com `CacheManager` para cache de resolução de ticker, listagem de documentos e detalhes de proventos
- Novos argumentos CLI: `--structured-earnings`, `--data-inicio`, `--data-fim`, `--output`
- Logging via `logging.getLogger(__name__)` e `LogPort` conforme padrão do projeto
- Testes com fixtures de HTML real, mocks de API e mock de repository
- Entidades expõem `to_text()` para alimentar VectorStore no `llm-chat`

## Capabilities

### New Capabilities

- `structured-earnings-domain`: Entidades de domínio — `Entidade`, `Provento` — e value objects `CNPJ`, `ISIN`, `ValorProvento`; protocolo `DocumentoIndexavel` com `to_text()`
- `ticker-resolution`: Resolução de ticker para `idFNET` via API `GetListClassFund` — infraestrutura compartilhada com `informe-mensal` e `llm-chat`. Retorna `None` para tickers sem dados na API de fundos
- `structured-earnings-extraction`: Pipeline completo de extração de rendimentos e amortizações estruturados (type=41) — listagem paginada de documentos + extração de detalhes via parsing HTML tabular + output JSON
- `structured-html-parsing`: Estratégias flexíveis de parsing de HTML tabular da B3 — extração por rótulo, parsing de tabelas por contexto, fallback regex

### Modified Capabilities

- `cli-interface`: Novos argumentos `--structured-earnings`, `--data-inicio`, `--data-fim`, `--output`

## Impact

- **Dependências**: Adição de `beautifulsoup4` ao `pyproject.toml`
- **Código afetado**: Novos módulos em `domain/structured/`, `application/`, `infrastructure/b3/`; extensão de `presentation/cli.py`
- **Cache**: Novos arquivos em `~/.cache/flowscope/` para resolução de ticker, listagens e detalhes
- **APIs**: Requisições a `sistemaswebb3-listados.b3.com.br/fundsListedProxy`
- **Ticker-agnóstico**: Qualquer ticker pode ser consultado; fontes retornam vazio quando não há dados
