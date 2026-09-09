## Why

O RFC-004 define 7 fontes de dados regulatórios e de mercado da B3 (censuras, condições excepcionais, programas de aquisição, notícias, fatos relevantes, avisos e assembleias), mas em formato monolítico sem adaptação à Clean Architecture do projeto. As outras RFCs (001, 002, 003) já foram traduzidas para changes com entidades de domínio, protocolos, use cases e integração com `llm-chat` via `to_text()` e `DocumentSource`. O RFC-004 é a peça faltante.

Além disso, a API `GetMaterialFacts` do RFC-004 é a **única fonte de dados regulatórios universal** — funciona para qualquer empresa listada na B3 (PETR4, VALE3, ITUB4), não apenas FIIs. As outras 3 changes (`structured-earnings`, `informe-mensal`, `documentos-relevantes`) são exclusivas de fundos. Sem esta change, o `llm-chat` ficaria incapaz de responder perguntas sobre fatos relevantes e assembleias de empresas não-FII, limitando severamente sua utilidade para o público-alvo do PRD (investidores do mercado acionário).

## What Changes

- Novas entidades de domínio em `domain/structured/`: `CensuraPublica`, `CondicaoExcepcional`, `NoticiaB3`, `FatoRelevante`, `Assembleia`, `AvisoAcionista`, `AvisoDebenturista`, `DocumentoMaterialFact`
- Value objects: `CodeCVM`, `DataBrasil`, `CategoriaDocumento`, `UrlDocumento`
- Protocolo `RegulacaoRepository` em `application/structured_ports.py` desacoplando a camada de aplicação das APIs B3 de regulação
- Nova resolução `ticker → codeCVM` compartilhada, análoga à resolução `ticker → idFNET` existente
- Novo método `listar_fatos_relevantes()` no `B3FundosClient` usando o endpoint `listedCompaniesProxy/CompanyCall/GetMaterialFacts` com token Base64 e paginação
- Novo método `listar_noticias()` no `B3FundosClient` usando o endpoint `PlantaoNoticias/Noticias/ListarTitulosNoticias`
- Parsing de HTML para Censuras Públicas, Condições Excepcionais e Programas de Aquisição via BeautifulSoup (reutilizando dependência existente)
- Use case `ExtrairDadosRegulatoriosUseCase` orquestrando os fluxos de extração
- Duas novas implementações de `DocumentSource` para o VectorStore do `llm-chat`: `MaterialFactsSource` (universal) e `NoticiasSource` (universal)
- `to_text()` em todas as entidades para integração com `llm-chat`
- Estratégia de cache com `CacheManager`: TTL 1 hora para notícias, 1 dia para fatos relevantes, 7 dias para censuras e condições
- Novos argumentos CLI: `--regulacao`, `--noticias`, `--fatos-relevantes`, `--categoria`
- Logging via `logging.getLogger(__name__)` conforme padrão do projeto

## Capabilities

### New Capabilities

- `regulacao-mercado-domain`: Entidades de domínio (`CensuraPublica`, `CondicaoExcepcional`, `NoticiaB3`, `FatoRelevante`, `Assembleia`, `AvisoAcionista`, `AvisoDebenturista`, `DocumentoMaterialFact`) e value objects (`CodeCVM`, `DataBrasil`, `CategoriaDocumento`, `UrlDocumento`); `to_text()` em todas as entidades para VectorStore
- `code-cvm-resolution`: Resolução de ticker para `codeCVM` via API `listedCompaniesProxy` — infraestrutura compartilhada com futuras changes que acessem dados CVM. Retorna `None` para tickers não listados
- `material-facts-extraction`: Pipeline de extração de Fatos Relevantes, Assembleias e Avisos via `GetMaterialFacts` — listagem paginada por categoria e codeCVM, mapeamento de categorias (1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, 48=Aviso Debenturistas, 107=Relatório Proventos), output JSON
- `noticias-extraction`: Pipeline de extração de notícias do Plantão B3 via `ListarTitulosNoticias` — filtro por data e palavra-chave, paginação, output JSON
- `regulacao-b3-extraction`: Pipeline de extração de Censuras Públicas, Condições Excepcionais e Programas de Aquisição via parsing HTML — extração por seletor CSS, fallback para campos não encontrados, output JSON
- `regulacao-document-sources`: Implementações de `DocumentSource` — `MaterialFactsSource` (universal, qualquer ticker) e `NoticiasSource` (universal) — para alimentar o VectorStore do `llm-chat`

### Modified Capabilities

- `cli-interface`: Novos argumentos `--regulacao`, `--noticias`, `--fatos-relevantes`, `--categoria`, `--palavra`

## Impact

- **Dependências**: Reutiliza `beautifulsoup4` (já adicionado por `structured-earnings`)
- **Código afetado**: Novos módulos em `domain/structured/` (extensão de `entities.py` e `value_objects.py`), `application/` (extensão de `structured_ports.py` e `structured_use_cases.py`), `infrastructure/b3/` (extensão de `funds_client.py` e `structured_parser.py`), novo `infrastructure/document_sources/` (extensão), `presentation/cli.py` (extensão)
- **Cache**: Novas chaves em `~/.cache/flowscope/` para resolução de codeCVM, notícias, fatos relevantes, censuras e condições
- **APIs**: Requisições a `sistemasweb.b3.com.br/PlantaoNoticias/` (notícias), `sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetMaterialFacts` (fatos relevantes), `www.b3.com.br/pt_br/regulacao/` (censuras e condições, HTML)
- **Ticker-agnóstico**: Qualquer ticker pode ser consultado; fontes retornam vazio quando não há dados. `GetMaterialFacts` funciona para todas as empresas listadas (não apenas FIIs)
- **Relação com `documentos-relevantes`**: `GetMaterialFacts` (universal, retorna metadados JSON com URLs CVM) complementa `GetReportsRelevants` (FII-only, retorna PDFs binários). São fontes de dados distintas para tipos de documento sobrepostos, sem conflito
