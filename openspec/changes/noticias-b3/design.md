## Context

Ver `proposal.md` — Why. A change `llm-chat` expõe a aba de chat única "Chat AI" e monta o contexto a partir do FlowScope, dos fundamentos, dos documentos e de fontes adicionais. A listagem de notícias já existe em `RegulacaoRepository.listar_noticias` (título, data, agência, URL), mas o corpo do artigo não é baixado, não há cache nem exibição dedicada. A sub-aba "Documentos" já oferece o padrão de árvore, pré-visualização e resumo por LLM a ser espelhado.

## Goals / Non-Goals

**Goals:**
- Sub-aba "Notícias" na Análise Geral, espelhando a experiência de "Documentos".
- Aquisição do corpo do artigo com cache próprio, progresso e cancelamento.
- Extração de texto e resumo curto/longo por LLM com cache.
- Notícias legíveis como fonte adicional de contexto da aba "Chat AI".

**Non-Goals:**
- Alterar a sub-aba "Documentos" ou a leitura de material facts.
- RAG vetorial (propriedade de `llm-chat-rag`).
- Persistência de sessão de chat (propriedade de `llm-chat`).

## Decisions

### 1. Reuso do padrão de aquisição de documentos

A aquisição segue `AquisicaoDocumentos`: falha isolada por item, callback de progresso e observação de `CancellationToken`. O download do artigo é injetável (como `baixar_pdf_cvm`), facilitando testes.

Alternativa considerada: reutilizar a listagem apenas com metadados — descartada, pois não produz resumo com valor.

### 2. Chave surrogate estável por notícia

A chave é `sha1(url)` quando há URL; caso contrário, `sha1(data|agencia|titulo)`. Evita depender de IDs instáveis e cobre notícias sem URL.

### 3. Cache `noticias/<AAAA>/<MM>/<hash>.html` e reuso dos stores

O HTML é gravado sob a raiz de cache, de modo que a chave relativa alimenta os stores existentes de texto e resumo. Assim o Chat lê as notícias com o mesmo leitor usado para documentos, e não é preciso uma store nova.

Alternativa considerada: store dedicada para notícias — descartada por duplicar a lógica de leitura/gravação.

### 4. `NoticiasPanel` irmão de `DocumentTreePanel`

O painel é um widget novo que reutiliza `ReadonlyText`, o serviço de resumo e o padrão de barra de botões, sem refatorar o painel de documentos (que permanece intacto e com seus testes).

### 5. Localização na Análise Geral

As notícias são globais (mercado), então a sub-aba vive na Análise Geral, coerente com a natureza do dado.

### 6. Escopo da fonte de notícias

As notícias são globais (mercado) e entram como fonte adicional de contexto da aba única "Chat AI", cobrindo o período disponível. Não há seletor de escopo nem filtro prévio por palavra: o ticker referido na pergunta é inferido pela LLM, que seleciona as notícias relevantes. Como o ticker só é conhecido após a leitura da pergunta, a filtragem acontece no modelo, não na montagem do contexto.

### 7. Integração via ponto de extensão do llm-chat

A `llm-chat` expõe um ponto de extensão para fontes adicionais de contexto. Esta change registra as notícias como fonte adicional, sem reordenar a cascata de documentos.

## Risks / Trade-offs

- **[Risco] Corpo do artigo não é HTML server-rendered** → spike de verificação antes de fixar a extração; se necessário, ajustar a estratégia ou degradar para metadados.
- **[Risco] Muitos downloads** → progresso, cancelamento, tolerância por item e um intervalo mínimo entre requisições.
- **[Risco] URL ausente ou duplicada** → chave surrogate e deduplicação no cache.
- **[Trade-off] Dependência de rede no corpo** → artigos indisponíveis ficam sem texto/resumo, sem quebrar a sub-aba.
- **[Trade-off] Filtro por ticker no modelo** → as notícias do período entram no contexto e a LLM seleciona as relevantes pela pergunta; um ticker sem menção textual pode perder notícias correlatas.

## Migration Plan

1. Confirmar que a `llm-chat` expõe o ponto de extensão de contexto.
2. Implementar listagem + aquisição/cache do corpo.
3. Implementar `NoticiasPanel` (árvore, preview, resumos).
4. Integrar as notícias ao contexto da aba "Chat AI" via ponto de extensão.
5. Rollback: mudanças aditivas; remover a sub-aba não afeta as demais.

## Open Questions

- As notícias compartilham o orçamento global de contexto do chat ou têm teto próprio? (resolvível na implementação, sem alterar specs)
