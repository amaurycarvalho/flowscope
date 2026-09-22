## Context

Ver `proposal.md - Why`. O estado atual que molda o desenho:

- A extração de texto vive em `presentation/gui/charts/document_preview.py`: `texto_de_pdf` (`pypdf`), `texto_de_html` (`BeautifulSoup`) e `texto_preview`, que devolve string vazia em falha ou ausência de texto. O marcador `SEM_TEXTO = "Sem texto extraível para pré-visualização."` já existe ali (`document_preview.py:17`), mas é aplicado apenas na exibição (`document_tree_panel.py:377`).
- `DocumentTreePanel` mantém `_preview_cache: dict[Path, str]` apenas em memória (`document_tree_panel.py:86`), limpo em `_limpar()`. O fluxo é `_iniciar_preview` → thread `_trabalhar` → `_aplicar_preview` (`document_tree_panel.py:282-354`).
- `DocumentSummaryService.precisa_resumo`/`resumo_para_exibir` decidem o resumo com `bool((texto or "").strip())` (`document_summary.py:69-91`). Como o marcador é não-vazio, gravá-lo como texto do cache faria a LLM rodar sobre o marcador se essa guarda não for corrigida.
- O padrão de persistência por ticker já existe em `infrastructure/document_summaries.py` (JSON por ticker, chave `chave_documento`, escrita atômica via `_atomic_write_bytes`, tolerância a ausência/corrupção). `DocumentCatalog` enriquece entradas no scan (`document_catalog.py:115,132`), mas o texto é grande demais para carregar no scan.
- A barra de rolagem vertical da árvore e do campo de texto já é criada (`document_tree_view.py:26`, `document_tree_panel.py:146`), porém não é mapeada: o conteúdo é empacotado antes da barra e, quando o painel é mais estreito que a largura requisitada do conteúdo, a barra é espremida para fora (`mapped=0, w=1` medido no painel real). O `FundamentalTablePanel` usa `grid` com pesos e não sofre disso (`fundamental_table.py:107-155`).
- A change `fii-guidance-informacoes-adicionais` ainda não foi implementada e hoje desenha o gatilho sobre `texto_preview` direto (`design.md:38`); é o momento de apontá-lo para o cache.
- A change `centralizar-controle-cursor` define a autoridade única de estado ocupado (`presenter.busy()`) e o watchdog do job de documentos.

## Goals / Non-Goals

**Goals:**
- Persistir o texto original extraído por documento, sem resumo/análise, e reutilizá-lo nos acessos seguintes sem reconverter.
- Registrar o marcador de ausência quando não houver texto e curto-circuitar resumo LLM, guidance e qualquer processamento do texto.
- Tornar visível e funcional a barra de rolagem vertical da árvore e da pré-visualização.
- Deixar a change de guidance pronta para consumir o cache, declarando a dependência.

**Non-Goals:**
- Invalidar o cache quando o arquivo mudar no mesmo caminho (decidido: sem invalidação, como os resumos).
- Carregar os textos no scan do catálogo.
- Alterar o formato/limites do resumo ou o comportamento de abertura de documentos.
- Extrair guidance: isso permanece na change `fii-guidance-informacoes-adicionais`.

## Decisions

### 1. Store de texto por ticker (modelo de `document_summaries.py`)

Criar `JsonDocumentTextStore` em `infrastructure/document_texts.py`, gravando em `~/.cache/flowscope/document-texts/<TICKER>.json`, com o mapa `chave_documento → texto` (string). Escrita atômica via `_atomic_write_bytes`, `schema_version` e leitura tolerante a ausência/corrupção. O payload é exclusivamente o texto bruto (ou o marcador).

- **Por quê:** reaproveita um padrão consolidado, mantém a chave alinhada à dos resumos e a gravação atômica preserva os demais documentos.
- **Alternativas:** arquivo por documento (leitura mais preguiçosa, porém mais arquivos e fora do padrão); estender `JsonDocumentSummaryStore` (rejeitado: misturaria resumo e texto, contrariando "apenas o texto").

### 2. Leitura preguiçosa com memo de sessão

O texto é lido na seleção do documento, não no `DocumentCatalog.catalogo`. O `_preview_cache` em memória permanece como memo de sessão (write-through) para evitar reparse do JSON do ticker a cada seleção.

- **Por quê:** texto pode ser grande; carregá-lo no scan oneraria a montagem da árvore.
- **Alternativas:** enriquecer `DocumentoArquivo` no scan como os resumos (rejeitado pelo custo); ler o arquivo a cada seleção sem memo (rejeitado: reparse repetido).

### 3. Marcador de ausência e predicado `tem_texto()`

Manter `SEM_TEXTO` em `document_preview.py` e adicionar `tem_texto(texto) -> bool`, que é `False` para vazio/só espaços e para o marcador. Substituir `bool(texto.strip())` por `tem_texto(texto)` em `precisa_resumo`, `resumo_para_exibir` e em `_mostrar_documento`.

- **Por quê:** o marcador é não-vazio; sem um predicado único, cada consumidor repetiria a comparação e o resumo/guidance rodariam sobre o marcador.
- **Alternativas:** gravar string vazia e usar a presença da chave como sinal (rejeitado: o requisito pede o marcador explícito e "chave ausente" já significa não convertido); constante própria em cada camada (rejeitado: divergência).

### 4. Fluxo de seleção ciente do cache

Em `_iniciar_preview`: consultar o store; em *hit*, usar o texto (e pular a conversão); em *miss*, rodar a thread que converte, grava `texto` (ou `SEM_TEXTO` quando vazio) e só então decide o resumo com `tem_texto`. A gravação ocorre no worker, antes de publicar na fila.

- **Por quê:** o gatilho natural de conversão é a leitura, e a gravação antecipada garante que os acessos seguintes sejam *hit*.
- **Alternativas:** gravar apenas no botão "Atualizar" (rejeitado: o usuário pode nunca acioná-lo).

### 5. Supressão de processamento quando não há texto

Sem texto, `precisa_resumo` retorna `False` e `resumo_para_exibir` retorna `None`; a pré-visualização exibe o marcador. A abertura (`_abrir`, duplo clique, Enter) não depende do texto e permanece intacta. O gatilho de guidance (change dependente) lê o cache e usa `tem_texto` para decidir se avalia.

- **Por quê:** atende à regra de não processar texto inexistente, mantendo a abertura disponível.
- **Alternativas:** checar vazio apenas na exibição (rejeitado: não impede LLM/guidance).

### 6. Correção da barra de rolagem pela ordem de empacotamento

Empacotar a `ttk.Scrollbar` **antes** do conteúdo em `DocumentTreeView` e em `_build_preview` (ou migrar para `grid` com pesos). Vincular a roda do mouse (`<MouseWheel>`, `<Button-4>`, `<Button-5>`) como em `FundamentalTablePanel._vincular_roda`.

- **Por quê:** o `pack` aloca em ordem; com o conteúdo primeiro e request maior que o painel, a barra fica sem cavidade e não é mapeada. Medido: barra `mapped=0, w=1`; após inverter a ordem, `mapped=1, w=15`.
- **Alternativas:** `grid` com `rowconfigure/columnconfigure` (também correto, diff maior); reduzir o `width`/`height` do conteúdo (paliativo, não garante em todos os tamanhos).

### 7. Dependência de `centralizar-controle-cursor`

Implementar esta change depois daquela e apoiar-se na autoridade única de estado ocupado e no watchdog do job de documentos, sem criar um segundo mecanismo de cursor/estado para o carregamento da pré-visualização.

- **Por quê:** o carregamento da pré-visualização é operação em background; a política de cursor/estado passa a ter dono único, e um caminho paralelo reintroduziria o vazamento que aquela change elimina.
- **Alternativas:** gerir cursor localmente no painel (rejeitado: duplica a política).

### 8. Reconhecimento do cache pela change de guidance

Editar os artefatos de `fii-guidance-informacoes-adicionais` para que o gatilho leia o texto do cache (em vez de reextrair), não avalie quando `not tem_texto(texto)` e declare a dependência desta change.

- **Por quê:** cumpre o pedido de uma única fonte de texto e evita processamento sobre o marcador; a dependência expressa a ordem de implementação.

## Risks / Trade-offs

- **[Cache desatualizado se o arquivo mudar no mesmo caminho]** → aceito por decisão (sem invalidação), igual aos resumos; limpar `~/.cache/flowscope/document-texts` ou reimplementar invalidação futuramente.
- **[JSON por ticker pode ficar grande]** → memo de sessão evita reparse; se necessário, migrar para arquivo por documento sem alterar o contrato observável.
- **[Marcador vazando para LLM/guidance]** → predicado `tem_texto()` compartilhado + testes de supressão.
- **[Barra de rolagem em temas *overlay*]** → mapeamento explícito e teste de GUI (requer `DISPLAY`) verificando `winfo_ismapped()`/largura.
- **[Conflito com a change de cursor no mesmo painel]** → ordem de implementação declarada e reuso da autoridade central.

## Migration Plan

- Aditivo: novo diretório de cache criado sob demanda; cache ausente/corrompido tolerado (tratado como ausência).
- Rollback: remover a leitura/gravação do store e reverter a ordem de empacotamento; resumos e comportamento de abertura permanecem.

## Open Questions

- Migrar para um arquivo por documento caso o volume de texto por ticker se torne problemático — decidível na implementação sem alterar specs ou abordagem.
