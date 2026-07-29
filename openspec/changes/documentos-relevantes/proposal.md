## Why

O RFC-003 define a extração de documentos não estruturados (PDFs de Assembleias, Comunicados, Fatos Relevantes e Relatórios) de tickers listados na B3. Esta é a terceira fonte de documentos que alimentará o VectorStore do `llm-chat`, complementando `structured-earnings` (proventos, type=41) e `informe-mensal` (informes mensais, type=40). Mantida como change separada para isolar o domínio de PDFs (download binário, extração de texto, cache de arquivos) e o novo endpoint `GetReportsRelevants` da API B3.

## What Changes

- Novo método `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` no `B3FundosClient` usando endpoint `GetReportsRelevants` com iteração por 4 categorias (1=Fatos Relevantes, 2=Assembleias, 3=Comunicados, 7=Relatórios), paginação e cache
- Download de PDFs via `fnet.bmfbovespa.com.br` com validação de header `%PDF` e cache binário em `~/.cache/flowscope/pdfs/`
- Extração de texto via PyPDF2 com fallback para ignorar PDFs corrompidos
- Nova entidade `DocumentoRelevante` em `domain/structured/entities.py` com metadados e texto extraído
- `DocumentoRelevante.to_text()` para alimentar o VectorStore do `llm-chat`
- Ticker-agnóstico: retorna lista vazia quando resolução falha ou ticker não tem documentos

## Capabilities

### New Capabilities

- `documentos-relevantes-domain`: Entidade `DocumentoRelevante` com metadados (ticker, id_documento, categoria, descricao, data_referencia, data_entrega, url) e `to_text()` para VectorStore
- `documentos-relevantes-extraction`: Pipeline de extração de PDFs — listagem por categoria via `GetReportsRelevants`, download com validação, extração de texto via PyPDF2, cache binário, retorno vazio para tickers sem dados

### Modified Capabilities

_Nenhuma. Esta change adiciona ao `B3FundosClient` e `domain/structured/entities.py` sem modificar requisitos de specs existentes._

## Impact

- **Dependência**: Requer `structured-earnings` implementada (B3FundosClient, CacheManager, ticker-resolution)
- **Código**: Extensão de `infrastructure/b3/funds_client.py`, `domain/structured/entities.py`; sem novos módulos de aplicação (usa protocolos e use cases existentes)
- **Cache**: PDFs binários em `~/.cache/flowscope/pdfs/` com chave `pdf_{id_documento}`; listagem com cache TTL 1 dia
- **APIs**: Endpoint `GetReportsRelevants` no domínio `sistemaswebb3-listados.b3.com.br`; download de PDFs em `fnet.bmfbovespa.com.br`
- **Dependências**: PyPDF2 já está no grupo `[llm]`; nenhuma dependência nova exclusiva desta change
