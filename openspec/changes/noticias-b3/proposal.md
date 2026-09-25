## Why

O FlowScope lê as notícias do Plantão B3 apenas ao vivo, sem uma visão dedicada, sem cache do corpo dos artigos e sem acesso pelo chat. Esta change adiciona uma sub-aba "Notícias" na Análise Geral que adquire o corpo dos artigos, extrai o texto, gera resumos e disponibiliza esse conteúdo como fonte de contexto da aba de chat "Chat AI".

## What Changes

- Nova sub-aba **"Notícias"** na Análise Geral, com layout e botões semelhantes aos da sub-aba "Documentos" (árvore, pré-visualização, atualizar, abrir, resumir pendentes).
- Árvore organizada em **categorias de topo** — "Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações" — cada uma seguindo a mesma sub-estrutura **ano → mês → categoria → item** já usada. A "Geral" reúne as notícias do Plantão B3; as demais vêm da RFC-004.
- **"Geral"**: listagem das notícias do Plantão B3 limitada ao **último ano (12 meses)**, lida em janelas mensais (a API aceita no máximo 30 dias por consulta), mantendo **somente casos excepcionais de mercado** (whitelist mantida) e **sem os anúncios de distribuição**, e aquisição do **corpo** de cada artigo a partir da URL, tolerando falhas por item.
- **"Censuras Públicas"**, **"Condições Excepcionais"** e **"Programas de Aquisição de Ações"**: carregados com **histórico completo** da fonte (sem corte de 12 meses), pois essas páginas/endpoints entregam o conjunto inteiro em poucas requisições.
- Regra de conteúdo: quando o item tem **URL de download**, o corpo é baixado (Plantão B3); quando **não tem URL**, o próprio item é o conteúdo (censuras, condições e programas), gravado no mesmo cache de notícias para extração de texto e resumo.
- Cache próprio do HTML das notícias, independente do cache de listagem, e reuso dos caches de texto e de resumos da sub-aba "Documentos".
- **Carga inicial somente do cache local**: ao abrir a sub-aba, a árvore é montada a partir do índice de metadados e do HTML/resumos/textos já gravados, sem consultar a B3. A listagem e o download de novos itens ocorrem apenas no botão **"Atualizar"** (em segundo plano), o que evita travar a interface na troca de aba.
- **Status por categoria**: durante o "Atualizar", a barra de status anuncia e acompanha cada categoria ("Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral") antes e durante a carga.
- **Carga parcial preservada**: os metadados são indexados a cada item processado, de modo que interromper a carga mantém e exibe na árvore o que já foi carregado.
- **Corpo do artigo da "Geral"**: a pré-visualização e o resumo usam o corpo do artigo (`#conteudoDetalhe`) da página do Plantão B3, sem a moldura de busca/navegação da página.
- **Documento vinculado sob demanda**: quando o corpo da notícia "Geral" é apenas um apontador para um documento (ex.: "Esclarecimentos de questionamentos CVM/B3" com URL da CVM RAD), o conteúdo é baixado ao selecionar a notícia e ao processar "Resumir pendentes", extraído e cacheado; captcha habilitado ou falha mantém o corpo original.
- **Carga incremental da "Geral" dia a dia**: a leitura do último ano é feita um dia por vez, do mais recente ao mais antigo. O dia mais recente é sempre recarregado (notícias novas) e marcadores persistidos (data mais antiga processada e referência da última carga) evitam reler os dias já baixados com sucesso.
- **Escritas do índice agrupadas**: as fontes regulatórias e a "Geral" gravam o índice em lotes e ao final, em vez de regravá-lo a cada item/dia; em cancelamento, os registros acumulados são preservados.
- **Árvore de notícias expandida só até o primeiro nível**: ao carregar, a raiz fica aberta e as categorias de topo recolhidas; anos, meses, tipos e itens ficam fechados, com expansão manual.
- Extração de texto (HTML → texto) e geração de resumo curto/longo via LLM, com botão "Resumir pendentes".
- Pré-visualização do conteúdo e abertura do artigo no navegador (quando houver URL).
- Disponibilização do conteúdo como fonte adicional de contexto da aba "Chat AI", cobrindo as quatro categorias; o ticker referido na pergunta é inferido pela LLM, sem seletor de escopo.

## Capabilities

### New Capabilities

- `noticias-acquisition`: listagem das notícias e aquisição/cache do corpo dos artigos.
- `noticias-panel`: sub-aba "Notícias" com árvore, pré-visualização, resumos e botões.
- `noticias-chat-context`: disponibilização das notícias como fonte adicional de contexto da aba "Chat AI".

### Modified Capabilities

## Impact

- **Depende de**: `llm-chat` (aba "Chat AI" e ponto de extensão de contexto) e `llm-core` (resumos via `LLMPort`).
- **Rede**: nova captação do corpo do artigo (além da listagem já existente em `RegulacaoRepository.listar_noticias`); leitura das páginas de censuras e condições excepcionais e do endpoint de programas de aquisição de ações (RFC-004).
- **Cache**: `~/.cache/flowscope/noticias/` para o HTML e para o índice de metadados (`noticias/index.json`); reuso de `document-texts/` e `document-summaries/`.
- **Domínio/Infra**: nova entidade `ProgramaAquisicao`; correção do parser de censuras (seletor real `li.accordion-navigation`) e do cabeçalho de condições excepcionais; `listar_programas_aquisicao` com retry (endpoint instável).
- **Binário**: inalterado (usa `requests`/`beautifulsoup` já presentes).
