## Why

O FlowScope lê as notícias do Plantão B3 apenas ao vivo, sem uma visão dedicada, sem cache do corpo dos artigos e sem acesso pelo chat. Esta change adiciona uma sub-aba "Notícias" na Análise Geral que adquire o corpo dos artigos, extrai o texto, gera resumos e disponibiliza esse conteúdo como fonte de contexto da aba de chat "Chat AI".

## What Changes

- Nova sub-aba **"Notícias"** na Análise Geral, com layout e botões semelhantes aos da sub-aba "Documentos" (árvore, pré-visualização, atualizar, abrir, resumir pendentes).
- Listagem das notícias do Plantão B3 no período e aquisição do **corpo** de cada artigo a partir da URL, tolerando falhas por item.
- Cache próprio do HTML das notícias, independente do cache de listagem, e reuso dos caches de texto e de resumos da sub-aba "Documentos".
- Extração de texto (HTML → texto) e geração de resumo curto/longo via LLM, com botão "Resumir pendentes".
- Pré-visualização do conteúdo e abertura do artigo no navegador.
- Disponibilização do conteúdo como fonte adicional de contexto da aba "Chat AI", cobrindo as notícias do período; o ticker referido na pergunta é inferido pela LLM, sem seletor de escopo.

## Capabilities

### New Capabilities

- `noticias-acquisition`: listagem das notícias e aquisição/cache do corpo dos artigos.
- `noticias-panel`: sub-aba "Notícias" com árvore, pré-visualização, resumos e botões.
- `noticias-chat-context`: disponibilização das notícias como fonte adicional de contexto da aba "Chat AI".

### Modified Capabilities

## Impact

- **Depende de**: `llm-chat` (aba "Chat AI" e ponto de extensão de contexto) e `llm-core` (resumos via `LLMPort`).
- **Rede**: nova captação do corpo do artigo (além da listagem já existente em `RegulacaoRepository.listar_noticias`).
- **Cache**: `~/.cache/flowscope/noticias/` para o HTML; reuso de `document-texts/` e `document-summaries/`.
- **Binário**: inalterado (usa `requests`/`beautifulsoup` já presentes).
