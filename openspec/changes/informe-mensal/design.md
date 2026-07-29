## Context

O RFC-002 descreve a extração de Informes Mensais Estruturados (type=40). A change `structured-earnings` estabelece a infraestrutura base: `B3FundosClient`, `CacheManager`, resolução de ticker, e parsing HTML. Esta change consome essa infraestrutura e adiciona o domínio específico do informe mensal, de forma ticker-agnóstica.

## Goals / Non-Goals

**Goals:**
- Entidades: `CarteiraAtivo`, `Carteira`, `Resultados`, `Indicadores`, `OutrasInformacoes`, `InformeMensal`
- Value object `Percentual`
- Protocolo `InformeMensalRepository` separado
- Parsing multi-tabela com classificação de contexto
- Validação cruzada como warning
- `InformeMensal.to_text()` para VectorStore
- CLI: `--informe-mensal`

**Non-Goals:**
- GUI, paralelismo, outros tipos de relatório

## Decisions

### 1. Protocolo separado: `InformeMensalRepository`

Domínios distintos — `ProventosRepository` lida com `DocumentoProvento`, `InformeMensalRepository` com `InformeMensal`. Ambos compartilham `B3FundosClient` via composição.

### 2. Classificação de tabelas por palavra-chave

Match case-insensitive de substrings no heading: `"carteira"`, `"resultado"`, `"indicador"`, `"outras"`. Fallback: `"geral"`.

### 3. Validação cruzada como warning

Divergências de totais logam `logger.warning`, ambos os valores preservados.

### 4. `InformeMensal.to_text()` para VectorStore

Representação textual completa para alimentar `llm-chat`.

### 5. Ticker-agnóstico

Pipeline retorna lista vazia quando resolução falha (ticker não-fundo).

## Risks / Trade-offs

- **[Risco] Layout HTML varia entre fundos** → Classificação por palavra-chave + fallback `"geral"`
- **[Trade-off] Depende de `structured-earnings`** → Ordem de implementação: structured-earnings → informe-mensal → llm-chat
