## 1. Pré-requisitos

- [x] 1.1 Verificar que a change `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `check_llm_deps`, exceções tipadas) e que o import funciona, com um teste de fumaça

## 2. Store de Resumos

- [x] 2.1 Implementar `JsonDocumentSummaryStore` em `infrastructure/document_summaries.py` com leitura/gravação em `~/.cache/flowscope/document-summaries/<TICKER>.json`, chave pelo caminho relativo à raiz de cache e escrita atômica, verificando com testes o round-trip por documento
- [x] 2.2 Tratar arquivo ausente e JSON corrompido na leitura, verificando com testes que ambos resultam em "sem resumos" sem erro
- [x] 2.3 Garantir que gravar o resumo de um documento preserva os resumos dos demais, verificando com teste de dois documentos

## 3. Catálogo de Documentos

- [x] 3.1 Adicionar `short_summary` e `long_summary` (default `None`) a `DocumentoArquivo`, verificando com teste que os campos existem e são nulos por padrão
- [x] 3.2 Injetar o store em `DocumentCatalog` e enriquecer cada entrada em `catalogo()`, verificando com testes os casos "documento com resumo" e "documento sem resumo"
- [x] 3.3 Verificar que a chave derivada do caminho relativo é estável entre varreduras (ex.: `bdr/ALZR11/2026/02/10.pdf`) com teste dedicado

## 4. Serviço de Resumo

- [x] 4.1 Implementar `ResumirDocumentoUseCase` e `ResumoDocumento` em `application/resumo_documento.py`, consumindo `LLMPort`, verificando com mock que uma única chamada é feita e que os dois resumos são retornados
- [x] 4.2 Montar o prompt com a fórmula XYZ e os limites de 280/1500, verificando com teste o conteúdo do prompt enviado
- [x] 4.3 Truncar os resumos para 280/1500 e limitar a entrada ao orçamento máximo, verificando com testes de fronteira
- [x] 4.4 Tratar texto vazio sem chamar a LLM e fazer parsing tolerante com fallback para resposta inteira, verificando com testes os casos vazio, formato esperado e formato inesperado
- [x] 4.5 Propagar as exceções tipadas da `llm-core` sem conversão, verificando com testes que `LLMUnavailableError` e `LLMCommunicationError` chegam ao consumidor

## 5. Widget de Texto Somente-Leitura

- [x] 5.1 Implementar `ReadonlyText` em `presentation/gui/widgets/readonly_text.py` com cursor visível e bloqueio de edição, verificando com testes que uma tecla de caractere não altera o conteúdo
- [x] 5.2 Garantir Ctrl+A e Ctrl+C e a navegação por Shift+setas no `ReadonlyText`, verificando com testes que a seleção e a cópia funcionam

## 6. Painel — Visão de Agrupamento

- [x] 6.1 Mapear os nós de agrupamento (ticker, ano, mês, categoria) no `DocumentTreePanel`, verificando com teste que um nó de agrupamento tem payload de agrupamento
- [x] 6.2 Renderizar a lista Markdown com níveis relativos (`#` no agrupamento selecionado, incrementando nos sub-agrupamentos) e um item por documento com o `short_summary`, verificando com testes a seleção de ticker e de categoria
- [x] 6.3 Aplicar a mensagem de indisponibilidade condicional (`Resumo indisponível.` + sufixo) conforme a LLM esteja configurada, verificando com testes os dois sufixos

## 7. Painel — Geração e Pré-visualização

- [x] 7.1 Compor a pré-visualização do documento como `long_summary` + linha em branco + `---` + linha em branco + texto integral, verificando com teste a composição exata
- [x] 7.2 Gerar os resumos sob demanda em thread de trabalho com estado de carregamento e persistência no store, verificando com `LLMPort` mockado que o catálogo do documento é atualizado e exibido
- [x] 7.3 Exibir a mensagem de indisponibilidade como `long_summary` quando a LLM não está configurada ou quando a geração falha, verificando com testes os casos "não configurada" e "exceção tipada"
- [x] 7.4 Descartar resultados obsoletos quando a seleção muda durante a geração, verificando com teste de troca de seleção concorrente

## 8. Testes e Quality Gate

- [x] 8.1 Atualizar os testes existentes do `DocumentTreePanel` para o novo comportamento de pré-visualização e verificar que a suíte passa
- [x] 8.2 Executar `make lint` e garantir que não há erros de linting no código novo
- [x] 8.3 Executar `pytest -m "not llm"` e garantir que a suíte base passa sem regressão
- [x] 8.4 Executar `openspec validate documentos-resumos` e garantir que a change permanece válida

## 9. Ajustes de Atalho e Cópia

- [x] 9.1 Vincular explicitamente Ctrl+A no `ReadonlyText`, cobrindo o mapeamento ausente no X11, verificando com teste que o atalho seleciona todo o conteúdo
- [x] 9.2 Fazer o botão "Copiar dados CSV" copiar o conteúdo do campo de texto quando a sub-aba "Documentos" estiver ativa, verificando com testes os casos "Documentos ativa" e "outra sub-aba"
- [x] 9.3 Habilitar o botão "Copiar dados CSV" na sub-aba "Documentos" mesmo sem dados da B3, verificando com teste o estado do botão

## 10. Persistência da Configuração de I.A.

- [x] 10.1 Fazer o botão "Salvar" do diálogo de I.A. gravar o bloco `llm.chat` e fechar a janela, verificando com teste que o diálogo deixa de existir após salvar
- [x] 10.2 Garantir que o fechamento da aplicação não sobrescreva o bloco `llm`: `load_preferences` carrega apenas as chaves de preferência e `save_preferences` faz *read-modify-write*, verificando com testes a preservação do bloco
- [x] 10.3 Verificar que a configuração salva é recarregada no próximo início e reaparece preenchida ao reabrir o diálogo, com teste de reabertura

## 11. Quality Gate

- [x] 11.1 Extrair `document_grouping.py` (Agrupamento, `render_grupo`, mensagem de indisponibilidade) e reduzir a complexidade de `render_grupo` de C para A
- [x] 11.2 Extrair `document_summary.py` (`DocumentSummaryService`) e `document_tree_view.py` (`DocumentTreeView`) do painel, elevando o MI de `document_tree_panel.py` de 17.2 para >= 30
- [x] 11.3 Reduzir a complexidade de `load_preferences` em `app.py` (rank C no xenon) extraindo `_ler_preferencias_salvas`
- [x] 11.4 Executar `make quality-gate` e garantir lint, complexidade, duplicação, testes, segurança e mutação aprovados
