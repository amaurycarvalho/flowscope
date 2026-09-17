## Context

Ver `proposal.md - Why`. Os documentos baixados ficam em raízes de cache por fonte: `bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf` (já implementado), `informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html` e `documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf` (changes de extração). A GUI já possui sub-abas por ticker (`TAB_CONFIGS`, `_build_ticker_tabs`, mapa `_TICKER`, `_do_update`) e um painel de fundamentos que lê apenas o cache histórico.

Esta change adiciona um catálogo que lê as raízes e um painel de árvore + pré-visualização.

## Goals / Non-Goals

**Goals:**
- Catálogo unificado por ticker/ano/mês/categoria, com tipo (`pdf`/`html`) e caminho.
- Sub-aba "Documentos" com árvore, pré-visualização textual e abertura no aplicativo padrão.
- Extração de texto sob demanda fora da thread da interface.
- Estado vazio e atualização manual.

**Non-Goals:**
- Alterar as raízes/layout dos caches das changes de extração.
- Indexação/VectorStore (pertence a `llm-chat`).
- Editar ou remover documentos em cache.
- Unificar fisicamente os caches em uma única árvore.

## Decisions

### 1. Catálogo por varredura das raízes, categoria derivada da fonte

**Decisão**: varrer `bdr/`, `informe-mensal/` e `documentos-relevantes/` e derivar a categoria da raiz; para documentos relevantes, ler a subpasta de categoria sob o mês.

**Alternativas**: (a) unificar fisicamente em `documentos/<TICKER>/...` — exigiria migrar o cache BDR e emendar uma change concluída; (b) índice de metadados dedicado — mais estrutura persistida. A varredura mantém os caches existentes intactos e atende à árvore pedida.

### 2. Painel único `DocumentTreePanel`

**Decisão**: um painel com `ttk.Treeview` à esquerda e `tk.Text` somente-leitura à direita. O nó raiz é o ticker; os níveis seguintes são ano, mês, categoria e arquivos.

**Alternativas**: lista plana com filtros — menos intuitiva para a hierarquia pedida. A árvore é o padrão da sub-aba e permite expandir/recolher.

### 3. Pré-visualização sob demanda em worker

**Decisão**: ao selecionar um arquivo, extrair o texto em uma thread de trabalho, exibindo "Carregando…"; cachear o texto em memória por caminho. HTML é convertido localmente (rápido); PDF usa `pypdf`.

**Racional**: a extração de PDF pode bloquear a thread do Tk em arquivos grandes. O debounce evita extrair no primeiro clique de um duplo-clique.

### 4. Abertura type-aware no aplicativo padrão

**Decisão**: helper cross-platform (`os.startfile` no Windows, `open` no macOS, `xdg-open` no Linux) acionado por duplo-clique, Enter ou botão "Abrir". PDF abre no leitor padrão; HTML no navegador.

### 5. Registro no notebook sem virar aba de indicadores

**Decisão**: adicionar "Documentos" à lista de sub-abas com um ramo dedicado em `_build_ticker_tabs` (como "Evolução dos Fundamentos"), registrá-la no mapa `_TICKER` e tratá-la em `_do_update`/`_deve_atualizar` para atualizar independentemente de haver dados B3 correntes.

### 6. Rótulo e ordenação

**Decisão**: arquivos exibidos pelo nome do arquivo (id) com a data do caminho; ano/mês decrescentes, categorias alfabéticas e arquivos do mais recente ao mais antigo.

### 7. Ticker compartilhado com a sub-aba "Evolução dos Fundamentos"

**Decisão**: a sub-aba "Documentos" exibe o mesmo ticker da sub-aba "Evolução dos Fundamentos": o ticker fixado por duplo-clique nos Fundamentos (`_evolution_ticker`) e, na sua ausência, o ticker selecionado na lista. Ambas usam um único helper `_ticker_apresentado()`.

**Alternativas**: (a) usar sempre o primeiro ticker selecionado — com uma watchlist inteira selecionada, o painel exibia um ticker arbitrário (o primeiro da lista) sem relação com o que o usuário estava analisando; (b) criar um estado de ticker próprio para documentos — duplicaria o estado de pin e divergiria das demais sub-abas por ticker. Compartilhar a fonte mantém as sub-abas coerentes e faz o pin dos Fundamentos refletir em Documentos.

**Racional**: o usuário relatou que a sub-aba parecia vazia porque apresentava um ticker diferente do que estava analisando. Sincronizar com a Evolução dos Fundamentos elimina a ambiguidade sem introduzir novo estado.

## Risks / Trade-offs

- **[Risco] Muitos arquivos por ticker** → A árvore com níveis de ano/mês/categoria mantém a navegação; a varredura é somente leitura.
- **[Risco] `pypdf` sem texto em PDFs escaneados** → Exibir mensagem informativa no preview, sem erro.
- **[Risco] Abrir arquivo com aplicativo inexistente** → Tratar falha de abertura com mensagem de status, sem interromper a interface.
- **[Trade-off] Sem título legível além do id** → O catálogo não depende de metadados externos; títulos podem ser enriquecidos no futuro.
- **[Trade-off] Raízes novas exigem atualização do catálogo** → Cada nova fonte deve registrar sua raiz e categoria no catálogo.

## Migration Plan

1. Implementar o catálogo de varredura e normalização.
2. Implementar o `DocumentTreePanel` (árvore, preview, abertura).
3. Registrar a sub-aba e o tratamento de atualização.
4. Rollback: remover a sub-aba e o painel restaura o comportamento atual; o catálogo é somente leitura.

## Open Questions

- Nenhuma pendente que afete specs, abordagem ou tarefas.
