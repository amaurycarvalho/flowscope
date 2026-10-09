## Context

Ver `proposal.md` — Why. A árvore da sub-aba "Documentos" é montada em `presentation/gui/charts/document_tree_view.py` (raiz = ticker, depois ano → mês → categoria → arquivo) e renderizada por `document_grouping.render_grupo`, com o despacho de clique em `document_tree_panel._on_select`. O `CatalogoTicker` (`domain/documents/entities.py`) modela apenas documentos.

O guidance vive no ledger (`infrastructure/guidance_store.py`), exposto por `GuidanceStore.avaliacoes(ticker)` e já lido, fora da thread do Tk, no worker de catálogo (`app_actions._submeter_leitura_documentos` chama `carregar_pendentes_guidance`). O catálogo e o ledger são relidos no worker; a thread do Tk apenas aplica o resultado (`aplicar_catalogo`).

A árvore de conhecimento do chat (`application/chat/arvore.py`) é um modelo paralelo, navegável por caminho, montado por `application/chat/montar.py` a partir de fontes (`FonteDocumentos`, `FonteNoticias`, ...) e descrito por `manifesto.py`. Hoje não há ramo de guidance nem de direitos/obrigações. `montar_arvore` (`chat_panel.py:302`) não passa `caminhos` para a assinatura de estado — a assinatura deriva só da watchlist.

O término do lote (`app_resumos_actions._finalizar_resumos_job`) só reavalia o botão; não remonta a árvore. As remontagens existentes usam o worker (`_submeter_leitura_documentos`/`_submeter_leitura_noticias`) e `noticias_actions._finalizar_noticias` já adia a remontagem com `after(0, ...)`.

## Goals / Non-Goals

**Goals:**
- Modelar três ramos na árvore de documentos sem alterar o `CatalogoTicker` (a estrutura de ramos vive na apresentação).
- Expor o guidance avaliado em modo somente-leitura, lido no worker, e navegá-lo na árvore e no chat.
- Introduzir os ramos placeholder de Direitos/Obrigações de forma forward-compatible.
- Remontar a árvore ao término do lote preservando a seleção.

**Non-Goals:**
- Alterar a avaliação de guidance, o formato do ledger ou a extração de documentos.
- Preencher Direitos/Obrigações com dados (changes futuras).
- Migrar dados ou mudar o cache.

## Decisions

### 1. Ramos modelados na apresentação, não no domínio

O `CatalogoTicker` permanece inalterado. A `DocumentTreeView` passa a montar a raiz do ticker com três filhos (Guidance, Documentos, Direitos e obrigações); a hierarquia de documentos fica sob o nó Documentos. Novo par de mapas na view: `grupos_guidance` (nó → filtro de ano/mês) e `guidances` (nó folha → entrada do ledger). Alternativa: estender o domínio com ramos de guidance. Rejeitada: o domínio de catálogo não deve conhecer apresentação nem o ledger.

### 2. Leitura do guidance no worker de catálogo

O worker que lê o catálogo (`carregar_pendentes_guidance`, em `document_flow_mixin.py`) passa a devolver também as entradas de guidance com valor, numa única leitura do ledger por ticker (`GuidanceStore.avaliacoes`). `app_actions._aplicar_catalogo_documentos` propaga `(catalogo, pendentes, guidances)` a `aplicar_catalogo`, que guarda `_guidances` em memória e monta a árvore. Alternativa: ler o ledger na thread do Tk ao montar. Rejeitada: viola a regra de não fazer I/O de cache na thread da interface.

### 3. FII identificado pelos documentos `Relatorio`

O ramo Guidance aparece quando o catálogo do ticker contém ao menos um documento da categoria `Relatorio` (própria de FII). Não se usa `classificar_ticker`, que sem a taxonomia/resolvedor devolve `DESCONHECIDO` para FIIs como `ALZR11`. FII sem entrada de guidance com valor exibe o ramo vazio. Alternativa: injetar o resolvedor de classificação no painel. Rejeitada: custo e acoplamento maiores que o sinal de cache já disponível.

### 4. Rótulo curado do RG e associação por `caminho_pdf`

Cada folha de guidance carrega a entrada do ledger. A associação com o RG usa `AvaliacaoGuidance.caminho_pdf` para localizar o documento no catálogo. O rótulo curado é `Relatório Gerencial — <mmm/aa> (<nome do arquivo>)`; sem o documento no catálogo, usa a data do relatório do ledger e o nome do arquivo do caminho registrado. A folha usa `formatar_guidance` no rótulo e no texto. Alternativa: usar a chave de conteúdo do ledger. Rejeitada: a chave não é resolvível para um nó da árvore, ao contrário do caminho.

### 5. Duplo-clique por índice reverso caminho → nó

A view mantém um índice reverso `caminho → nó` dos arquivos. No duplo-clique da folha de guidance, o painel localiza o nó do RG pelo caminho, expande os ancestrais, seleciona e faz `see`; se o RG não estiver no catálogo, não salta nem falha. Alternativa: varrer `_itens` a cada duplo-clique. Rejeitada: O(n) por clique e sem expansão dos ancestrais.

### 6. Placeholders forward-compatible

No chat, Direitos/Obrigações são folhas-placeholder com conteúdo explícito de ausência de dados (`no_folha`), pois no modelo de árvore "sem filhos = folha". Quando uma change futura adicionar filhos, o nó deixa de ser folha automaticamente. Alternativa: permitir nó interno vazio. Rejeitada: muda o invariante (`nó folha não tem filhos`) e o protocolo/`contar`/índice. Na GUI, os nós são grupos vazios que exibem a indicação de ausência de dados.

### 7. Expansão de primeiro nível por sessão

O painel guarda o conjunto de tickers já exibidos na sessão (`_tickers_expandidos`). Na primeira exibição de um ticker e a cada troca, monta a raiz aberta e os três ramos recolhidos; exibições seguintes preservam a expansão/seleção. Espelha `NoticiasTreeView.popular_secoes` (`open=False`).

### 8. Remontagem pós-lote disparada pelo host, seleção preservada

`_finalizar_resumos_job` passa a agendar `self.after(0, self._recarregar_painel_resumos)`, que despacha pela origem (`_resumos_continuar`): notícias → `_submeter_leitura_noticias`; documentos → `_submeter_leitura_documentos`. A remontagem reusa o caminho de leitura fora da thread do Tk. Para não perder o contexto, o painel separa "limpar nós" de "limpar pré-visualização/seleção": antes de remontar guarda o caminho selecionado, e após `popular` re-seleciona o nó e reexibe a pré-visualização (a leitura de texto continua no worker). Alternativa: reset simples. Rejeitada: apagaria a pré-visualização recém-recomposta pelo lote.

### 9. Chat: novas fontes, manifesto e assinatura

Novo `FonteGuidance` monta `/guidance/<ticker>/<ano>/<mes>/<folha>` (folha = texto formatado + rótulo do RG). `FonteDireitosObrigacoes` monta `/direitos-obrigacoes/{direitos,obrigacoes}` como placeholders. `montar_arvore` agrega as fontes, atualiza `manifesto.MAPA_ARVORE` e passa os caminhos do ledger de guidance em `caminhos`, para que a assinatura de estado invalide quando um guidance é gravado.

## Risks / Trade-offs

- **[Risco] Associação por `caminho_pdf` divergente** (documento movido ou cache diferente) → a folha ainda exibe o texto; o duplo-clique degrada sem salto, conforme a spec.
- **[Risco] `montar_arvore` não repassa `caminhos`** (hoje a assinatura deriva só da watchlist) → incluir o ledger nos caminhos nesta change; validar a invalidação do manifesto por teste.
- **[Trade-off] Uma leitura do ledger por ticker no worker** → aceitável (JSON pequeno, fora da thread do Tk); evita N leituras.
- **[Risco] Teto de 4.000 tokens do manifesto com mais ramos** → a degradação "só chaves" já existe; adicionar teste de regressão.
- **[Trade-off] Preservação de seleção exige separar limpeza de nós da limpeza de preview** → mais código no painel, porém evita o reset visual após o lote.
- **[Risco] Convivência com `guidance-preview-rg`** (em finalização) no mesmo painel/mixin → implementar depois de arquivá-la para reduzir conflito.

## Migration Plan

Sem migração de dados: o formato do ledger e do cache não muda. Rollback = reverter a montagem dos ramos, a exposição read-only e a remontagem pós-lote; nenhuma persistência nova.
