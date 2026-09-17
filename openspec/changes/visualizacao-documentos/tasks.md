## 1. Catálogo de documentos

- [x] 1.1 Definir as raízes de cache e o mapa raiz → categoria (`bdr` → "Aviso aos Acionistas", `informe-mensal` → "Informe Mensal", `documentos-relevantes` → subpasta de categoria)
- [x] 1.2 Implementar a varredura das raízes, ignorando raízes inexistentes
- [x] 1.3 Normalizar os arquivos na hierarquia ticker → ano → mês → categoria → arquivos, com tipo (`pdf`/`html`) e caminho
- [x] 1.4 Implementar a ordenação (ano/mês decrescentes, categorias alfabéticas, arquivos do mais recente ao mais antigo)
- [x] 1.5 Retornar estrutura vazia para ticker sem documentos, sem erro

## 2. Testes do catálogo

- [x] 2.1 Testar a consolidação de múltiplas raízes com diretório temporário
- [x] 2.2 Testar a derivação de categoria (raiz e subpasta) e a classificação de tipo
- [x] 2.3 Testar a ordenação e o ticker sem documentos
- [x] 2.4 Testar raiz inexistente sem erro

## 3. Painel de documentos

- [x] 3.1 Implementar `DocumentTreePanel` com `ttk.Treeview` (raiz = ticker; ano/mês/categoria/arquivos) e `tk.Text` somente-leitura
- [x] 3.2 Montar a árvore a partir do catálogo do ticker e tratar pasta (expandir/recolher) vs arquivo
- [x] 3.3 Implementar a pré-visualização sob demanda em worker, com estado "Carregando…", cache em memória e mensagem para arquivo sem texto
- [x] 3.4 Implementar o helper de abertura cross-platform e o acionamento por duplo-clique, Enter e botão "Abrir"
- [x] 3.5 Implementar o estado vazio e o controle de atualização

## 4. Testes do painel

- [x] 4.1 Testar a montagem da árvore a partir de um catálogo fixture
- [x] 4.2 Testar a derivação de texto de HTML e PDF (com mock do extrator)
- [x] 4.3 Testar a abertura type-aware (com mock do helper de sistema)
- [x] 4.4 Testar estado vazio e atualização

## 5. Integração no notebook

- [x] 5.1 Adicionar a sub-aba "Documentos" à "Análise do Ticker" com ramo dedicado em `_build_ticker_tabs`
- [x] 5.2 Registrar o painel no mapa `_TICKER` e tratar em `_do_update`/`_deve_atualizar` (atualiza sem depender de dados B3 correntes)
- [x] 5.3 Garantir a atualização ao trocar o ticker selecionado e adicionar o conteúdo explicativo da sub-aba

## 6. Quality Gate

- [x] 6.1 Executar `make lint` e corrigir avisos/erros
- [x] 6.2 Executar `make test` e garantir que todos os testes passam
- [x] 6.3 Executar `openspec validate visualizacao-documentos` e garantir que a change permanece válida
