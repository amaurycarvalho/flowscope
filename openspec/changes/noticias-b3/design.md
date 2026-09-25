## Context

Ver `proposal.md` — Why. A change `llm-chat` expõe a aba de chat única "Chat AI" e monta o contexto a partir do FlowScope, dos fundamentos, dos documentos e de fontes adicionais. A listagem de notícias já existe em `RegulacaoRepository.listar_noticias` (título, data, agência, URL), mas o corpo do artigo não é baixado, não há cache nem exibição dedicada. A sub-aba "Documentos" já oferece o padrão de árvore, pré-visualização e resumo por LLM a ser espelhado.

## Goals / Non-Goals

**Goals:**
- Sub-aba "Notícias" na Análise Geral, espelhando a experiência de "Documentos".
- Árvore com categorias de topo "Geral", "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações", cada uma na sub-estrutura ano → mês → categoria → item.
- Aquisição do corpo do artigo com cache próprio, progresso e cancelamento.
- Extração de texto e resumo curto/longo por LLM com cache.
- Notícias e informações regulatórias legíveis como fonte adicional de contexto da aba "Chat AI".

**Non-Goals:**
- Alterar a sub-aba "Documentos" ou a leitura de material facts.
- RAG vetorial (propriedade de `llm-chat-rag`).
- Persistência de sessão de chat (propriedade de `llm-chat`).
- Alterar a whitelist de eventos excepcionais da categoria "Geral".

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

### 8. Janela de 12 meses em lotes de 30 dias e whitelist de casos excepcionais

A leitura é limitada ao **último ano** (365 dias) e feita em **lotes de até 30 dias**, porque a API do Plantão B3 aceita no máximo 30 dias por consulta (ver decisão 18 para a carga incremental). A listagem acumula e deduplica os lotes por chave estável. O objetivo da sub-aba é mostrar **somente casos excepcionais fora da curva**, então a listagem passou a ser por **inclusão** (whitelist): só passam notícias cujo título corresponde a um evento de mercado relevante (suspensão/reabertura/retirada de negociação, negociação não contínua, início/prorrogação/liberação de negociação, incorporação/fusão/cisão/reorganização, recuperação judicial/extrajudicial, falência, liquidação, intervenção, grupamento/desdobramento/bonificação, redução/aumento de capital, subscrição privada, amortização, deslistagem/cancelamento de listagem, oferta pública/OPA e modificações de oferta, aquisição/alienação de participação, mudança de auditor, ato homologatório, transação entre partes relacionadas, esclarecimentos CVM/B3 e oscilação atípica). Os **anúncios de distribuição foram retirados** da whitelist. A correspondência é insensível a caixa e acentos e usa fronteira de palavra (a sigla `OPA` não casa com “administração para”). O filtro fica na listagem, de modo que nem a aquisição nem o catálogo/exibição consideram notícias rotineiras. Essa decisão substitui o filtro anterior por exclusão de títulos administrativos.

**Decisão aprovada (filtro da "Geral"):** a whitelist de eventos excepcionais é **mantida como está**; a lista revisada em 9.8 é a vigente. Não há ampliação nem restrição de termos nesta change.

### 9. Categorias de topo na árvore, sem alterar os níveis existentes

A árvore ganha um nível acima do catálogo atual: "Notícias" (raiz) → categoria de topo ("Geral", "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações") → ano → mês → categoria → item. Em vez de introduzir um quinto nível genérico em `CatalogoTicker`, a change cria `CatalogoNoticias`/`SecaoNoticias`, em que cada seção é um `CatalogoTicker` (com `ticker` = nome da seção) e a raiz agrega as seções. A árvore de notícias estende `DocumentTreeView` para inserir a raiz e reaproveitar a inserção ano → mês → categoria por seção. O nível "categoria" (3º) passa a ser específico da fonte: **tipo de notícia** na "Geral" (ver decisão 17), ticker/emissor em censuras, segmento em condições e empresa em programas.

Alternativa considerada: adicionar um nível "secao" a `CatalogoTicker`/`render_grupo` — descartada por espalhar mudanças na árvore de documentos (que permanece intacta).

### 10. Histórico completo das três fontes regulatórias

Censuras, condições excepcionais e programas de aquisição são carregados com o **histórico completo** da fonte, sem o corte de 12 meses da "Geral". Essas fontes entregam o conjunto inteiro em poucas requisições (uma página de censuras, uma de condições e um endpoint paginado de programas), então o custo de rede é praticamente fixo e independente do volume. Medição em 25/09/2026: censuras 144 (1 nos últimos 12 meses), condições 22 (8), programas 111 (91 iniciados nos últimos 12 meses). O agrupamento ano → mês mantém a navegação utilizável.

### 11. Item unificado e regra de conteúdo (URL vs. o próprio item)

A aquisição e o catálogo passam a trabalhar com `ItemNoticia` (seção, título, data, categoria, URL opcional e conteúdo opcional), convertido a partir das quatro fontes. A chave é `sha1(URL)` quando há URL e, sem URL, `sha1(chave-base estável do item)`. Quando há URL, o corpo é baixado (Plantão B3); quando não há, o próprio registro é o conteúdo e é gravado como HTML mínimo no mesmo cache `noticias/<AAAA>/<MM>/<hash>.html`, de modo que a extração de texto, a pré-visualização e o resumo reutilizem o pipeline de "Documentos" sem código novo.

### 12. Fontes HTML/JSON da RFC-004

- **Censuras Públicas**: a página real usa `li.accordion-navigation` (título com emissor, ticker e data; conteúdo em vários parágrafos), e não `div.item-censura` — o parser é corrigido e passa a concatenar os parágrafos.
- **Condições Excepcionais**: a tabela real traz o cabeçalho em células de dados; o parser passa a ignorar a linha de cabeçalho.
- **Programas de Aquisição de Ações**: a página embute um app Angular que chama `stockProgramProxy/StockProgramCall/GetListedCompany/<base64>`. O endpoint responde **404 de forma intermitente** (~30%), então a leitura usa retry com pequena espera antes de desistir por item.

### 13. "Geral" por último na árvore e no processamento

A categoria "Geral" é a carga pesada: um download de artigo por item na aquisição e, depois, um resumo por item. As três fontes regulatórias são leves (poucas requisições, sem download por item). Por isso "Geral" é posicionada **por último** tanto na ordem das categorias de topo da árvore (`SECOES_ORDEM`) quanto na ordem em que `listar_itens` monta os itens. Assim, "Atualizar" (carga) e "Resumir pendentes" (extração de texto e resumo) processam primeiro censuras, condições e programas, e só então a "Geral". A ordem é a mesma em `SECOES_ORDEM`, de modo que a árvore e o processamento permanecem coerentes.

### 14. Catálogo somente-leitura do cache local

Ao trocar para a sub-aba "Notícias", o painel remontava a árvore chamando `NoticiasCatalog.secoes()` → `listar_itens()` → repositório da B3 (janelas mensais + fontes regulatórias). Ainda que a listagem seja cacheada em HTTP, a chamada rodava na thread do Tk e congelava a interface até responder (ou expirar o timeout de cada janela). O mesmo valia para a fonte de contexto do chat.

A carga inicial passa a ler **somente o cache local** e o botão "Atualizar" é o único caminho de rede, espelhando a sub-aba "Documentos". Como o caminho do HTML (`noticias/<AAAA>/<MM>/<hash>.html`) não carrega título, seção, categoria, data nem URL, a aquisição grava esses metadados em um **índice** (`NoticiasIndexStore`, `noticias/index.json`). `NoticiasCatalog` passa a combinar o índice com o HTML existente e enriquece os resumos pelo `JsonDocumentSummaryStore`, sem depender do repositório. O painel e o `FonteNoticias` não conhecem mais a B3.

A migração é tolerante: HTML já cacheado sem índice é indexado na próxima execução de "Atualizar", pois `AquisicaoNoticias._persistir` registra os metadados mesmo quando o corpo já existe e não é baixado de novo.

Alternativa considerada: executar a listagem em thread de trabalho — descartada por manter ida à rede no fluxo de exibição, contrariando o espelhamento com "Documentos" e mantendo a dependência de disponibilidade da B3 para simplesmente abrir a aba.

### 15. Status por categoria, carga parcial e corpo do artigo

Três ajustes de usabilidade/qualidade fecharam lacunas da primeira versão:

1. **Status por categoria:** a listagem acontecia inteira (censuras, condições, programas e 12 janelas da "Geral") antes de qualquer progresso, e o rótulo era genérico. A aquisição passou a consumir `fontes_noticias`, que expõe cada fonte como carga preguiçosa na ordem de exibição; antes de listar cada uma, anuncia `• Carregando <categoria>…` e, em seguida, reporta o progresso por item com o nome da categoria.
2. **Carga parcial:** o índice era gravado só ao final (no `finally`), então interromper a carga deixava a árvore desatualizada — o painel era remontado antes do flush. O índice passou a ser gravado a cada item processado, de modo que a remontagem imediata após o cancelamento exibe o que já foi carregado.
3. **Corpo do artigo:** `texto_de_html`/`texto_preview` ganharam um seletor opcional. As notícias da "Geral" usam `#conteudoDetalhe` (corpo do artigo do Plantão B3), evitando que a pré-visualização e o resumo capturem a moldura de busca, o rodapé e "Visualizar Todas Notícias". Itens regulatórios, sem esse elemento, caem no texto da página inteira.

Alternativa considerada (status): anunciar só um rótulo genérico — descartada por não informar qual categoria está em carga.

### 16. Documento vinculado baixado sob demanda

Algumas notícias da "Geral" não trazem o conteúdo no corpo: o `#conteudoDetalhe` é apenas um apontador em **texto puro** (não um `<a href>`) para o documento. Casos típicos são "Esclarecimentos de questionamentos CVM/B3", cujo corpo é a URL do visualizador da CVM RAD. O sistema baixava a página do Plantão B3 e parava aí.

Decisão: resolver o documento **sob demanda** — na pré-visualização (seleção) e no processamento de "Resumir pendentes" —, nunca durante a listagem. `noticias_vinculo.baixar_conteudo_vinculado` detecta a URL suportada no corpo e a resolve; `NoticiasPanel._texto_do_arquivo` anexa o texto ao corpo e `preparar_texto` o persiste no cache de textos, de modo que seleções/resumos seguintes não rebaixam.

O visualizador da CVM RAD não serve o arquivo por GET: devolve um HTML com `<iframe id="pdfViewer">` e obtém o PDF por um POST AJAX ao WebMethod `frmExibirArquivoIPEExterno.aspx/ExibirPDF`, que retorna o PDF em **base64**. O resolvedor faz GET (cookie de sessão) + POST com `{codigoInstituicao, numeroProtocolo, token, versaoCaptcha}`, decodifica o base64 e extrai o texto com `pypdf` (reuso de `bdr/text.extrair_texto`). Se `hdnHabilitaCaptcha == 'S'`, ou se o WebMethod responde `V2`/`:ERRO:`, o download é ignorado e mantém-se o corpo — evitando quebrar a pré-visualização.

Alternativa considerada: baixar automaticamente na aquisição — descartada por multiplicar as requisições (cada documento exige GET+POST) e por baixar conteúdo que talvez nunca seja lido. Alternativa considerada: seguir qualquer URL do corpo — descartada por fragilidade e risco; só o padrão CVM RAD é resolvido.

### 17. Agrupamento da "Geral" por tipo de notícia

O terceiro nível da árvore da "Geral" era a **agência** (sempre "18"/"Plantão B3"), o que produzia um único grupo inútil sob cada mês. Ele passa a ser o **tipo de notícia**, de modo que a hierarquia fica ano → mês → tipo → item. O tipo é derivado do título por `classificar_tipo`, que reusa a normalização (caixa/acentos/fronteira de palavra) da whitelist, e é materializado como a `categoria` do item na aquisição (e, portanto, persistido no índice).

Classificação sugerida, cobrindo toda a whitelist; títulos que não casam vão para **"Outros"**:

| Tipo | Termos da whitelist |
| --- | --- |
| Negociação | suspensão/revogação/reabertura/retirada de negociação, negociação não contínua, início/prorrogação/adiamento, alteração do nome de pregão, deixam de ser negociadas |
| Listagem e Registro | suspensão/cancelamento de registro, cancelamento de listagem, deslistagem, conversão de categoria |
| Ofertas e OPA | oferta pública/ações, OPA, modificação de oferta, direito de preferência |
| Participações | aquisição/alienação de participação |
| Reorganização Societária | incorporação, fusão, cisão, reorganização |
| Recuperação e Liquidação | recuperação judicial/extrajudicial, pedido/proc. recuperação, falência, liquidação, liquidação extrajudicial, intervenção |
| Eventos de Capital | grupamento, desdobramento, bonificação, redução/aumento de capital, amortização |
| Governança e Auditoria | mudança de auditor, ato homologatório, transação entre partes relacionadas |
| Esclarecimentos e Oscilações | esclarecimentos, solicitou esclarecimentos, oscilação atípica |
| Outros | (fallback) |

A ordem dos tipos define a prioridade quando mais de um termo casa. Só a "Geral" muda: as seções regulatórias mantêm o agrupamento por ticker/segmento/empresa. Como o tipo passou a compor a `categoria` persistida no índice, o cache do "Geral" foi limpo para que a próxima carga o regenere com os tipos.

Alternativa considerada: agrupar pelo dia da notícia — descartada por gerar muitos grupos de um único item e não ajudar a navegação.

### 18. Carga incremental da "Geral" dia a dia

Recarregar o ano inteiro a cada "Atualizar" é caro. A "Geral" passou a ser carregada **um dia por vez**, do mais recente ao mais antigo, e o índice guarda **duas datas** (`noticias/index.json`): a **data mais antiga já processada** (`geral_mais_antiga`) e a **referência da última carga** (`geral_referencia`). A cada carga:

- o **dia mais recente** é **sempre recarregado**, captando notícias novas e retificações;
- preenche-se a eventual **lacuna** entre a referência anterior e o dia mais recente (quando a data de referência avançou), dia a dia;
- retrocede-se a partir de `geral_mais_antiga` dia a dia até completar ~1 ano, cobrindo cargas anteriores interrompidas;
- os marcadores são atualizados a cada dia processado com sucesso (inclusive dias sem notícia excepcional) e a referência só avança quando o primeiro dia conclui; um dia com falha interrompe a retomada sem marcá-lo, para ser refeito depois.

O custo da primeira carga (cache frio) sobe para uma consulta por dia do ano; em contrapartida, execuções seguintes só releem o dia mais recente e eventuais lacunas, e dias já baixados com sucesso são pulados individualmente (sem refazer janelas inteiras).

**Gravação do índice em lotes:** tanto as fontes regulatórias (item a item) quanto a "Geral" (dia a dia) acumulam os registros e gravam o índice a cada 25 unidades e ao final, em vez de regravar o arquivo a cada item/dia. Em cancelamento, os itens já processados são gravados; no caso da "Geral", sem marcar o dia, para que ele seja retomado.

Alternativa considerada: lotes de 30 dias — substituída nesta revisão por granularidade diária, que permite pular exatamente os dias já obtidos. Alternativa considerada: decidir o pulo pela presença de notícias no cache — descartada porque dias legitimamente vazios seriam relidos para sempre; os marcadores de sucesso cobrem esse caso.

### 19. Árvore de notícias expandida só até o primeiro nível

Ao carregar (inicial ou após "Atualizar"), a árvore de notícias é exibida expandida **somente até o primeiro nível**: a raiz "Notícias" fica aberta e as categorias de topo ficam recolhidas; anos, meses, tipos e itens permanecem fechados. Isso evita abrir centenas de nós de uma vez. `DocumentTreeView.popular_catalogo` ganhou o parâmetro `abrir` (padrão `True`, preservando "Documentos"), e a árvore de notícias passa `abrir=False`. A expansão continua manual a partir daí.

Alternativa considerada: abrir também as categorias (mostrando os anos) — descartada por já exibir muitos nós em períodos longos.

## Risks / Trade-offs

- **[Risco] Corpo do artigo não é HTML server-rendered** → spike de verificação antes de fixar a extração; se necessário, ajustar a estratégia ou degradar para metadados.
- **[Risco] Muitos downloads** → progresso, cancelamento, tolerância por item e um intervalo mínimo entre requisições.
- **[Risco] URL ausente ou duplicada** → chave surrogate e deduplicação no cache.
- **[Trade-off] Dependência de rede no corpo** → artigos indisponíveis ficam sem texto/resumo, sem quebrar a sub-aba.
- **[Trade-off] Filtro por ticker no modelo** → as notícias do período entram no contexto e a LLM seleciona as relevantes pela pergunta; um ticker sem menção textual pode perder notícias correlatas.
- **[Trade-off] Índice como fonte da árvore** → se o índice for apagado ou corrompido, a sub-aba fica vazia até o próximo "Atualizar", que o reconstrói sem rebaixar os corpos já em cache; entradas de índice sem HTML são ignoradas na leitura.
- **[Risco] Endpoint de programas instável (404 intermitente)** → retry com espera; em falha persistente a seção fica indisponível sem derrubar as demais.
- **[Risco] Parser de censuras/condições quebra com mudança de layout** → extração tolerante retorna lista vazia e a seção apenas não aparece.

## Migration Plan

1. Confirmar que a `llm-chat` expõe o ponto de extensão de contexto.
2. Implementar listagem + aquisição/cache do corpo.
3. Implementar `NoticiasPanel` (árvore, preview, resumos).
4. Integrar as notícias ao contexto da aba "Chat AI" via ponto de extensão.
5. Rollback: mudanças aditivas; remover a sub-aba não afeta as demais.

## Spike de pré-requisitos

- **Ponto de extensão do contexto (`llm-chat`)**: confirmado. `ContextoChat.fontes_adicionais` (`application/chat/consultar.py`) e o parâmetro `ChatPanel(fontes_adicionais=...)` (`presentation/gui/chat/chat_panel.py`) permitem registrar uma fonte adicional como `FonteContexto(titulo, texto)`, renderizada como seção própria antes da pergunta. As notícias entram por esse ponto, sem alterar a cascata de documentos.
- **Corpo do artigo server-rendered**: confirmado. A página `PlantaoNoticias/Noticias/Detail?agencia=18&idNoticia=<id>&dataNoticia=<AAAA-MM-DD>` retorna HTML server-rendered com o corpo em `<pre id="conteudoDetalhe">`, extraível com o mesmo `texto_de_html` usado no painel de documentos. O endpoint de listagem `ListarTitulosNoticias` devolve itens `{"NwsMsg": {...}}` (`headline`/`dateTime`/`id`) sem URL explícita; a conversão de `RegulacaoRepository.listar_noticias` passou a desembrulhar o `NwsMsg` e derivar a URL da página `Detail` a partir do id e da data, de modo que as notícias do período chegam com URL preenchida. Notícias sem id/URL continuam sendo ignoradas na aquisição (conforme a spec).
- **Fontes da RFC-004**: confirmado em 25/09/2026. Censuras usam `li.accordion-navigation` (144 itens); condições usam tabela com 22 linhas de dados (8 nos últimos 12 meses); programas usam `stockProgramProxy/StockProgramCall/GetListedCompany` (111 em andamento, 91 iniciados em 12 meses) com 404 intermitente. Nenhuma das três tem URL de conteúdo por item.

## Open Questions

- As notícias compartilham o orçamento global de contexto do chat ou têm teto próprio? (resolvido na implementação com um teto próprio de caracteres, sem alterar specs)
