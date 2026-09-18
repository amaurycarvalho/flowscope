## 1. Pré-requisitos

- [ ] 1.1 Verificar que a change `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `check_llm_deps`, exceções tipadas) e que o import funciona, com um teste de fumaça

## 2. Store de Resumos

- [ ] 2.1 Implementar `JsonDocumentSummaryStore` em `infrastructure/document_summaries.py` com leitura/gravação em `~/.cache/flowscope/document-summaries/<TICKER>.json`, chave pelo caminho relativo à raiz de cache e escrita atômica, verificando com testes o round-trip por documento
- [ ] 2.2 Tratar arquivo ausente e JSON corrompido na leitura, verificando com testes que ambos resultam em "sem resumos" sem erro
- [ ] 2.3 Garantir que gravar o resumo de um documento preserva os resumos dos demais, verificando com teste de dois documentos

## 3. Catálogo de Documentos

- [ ] 3.1 Adicionar `short_summary` e `long_summary` (default `None`) a `DocumentoArquivo`, verificando com teste que os campos existem e são nulos por padrão
- [ ] 3.2 Injetar o store em `DocumentCatalog` e enriquecer cada entrada em `catalogo()`, verificando com testes os casos "documento com resumo" e "documento sem resumo"
- [ ] 3.3 Verificar que a chave derivada do caminho relativo é estável entre varreduras (ex.: `bdr/ALZR11/2026/02/10.pdf`) com teste dedicado

## 4. Serviço de Resumo

- [ ] 4.1 Implementar `ResumirDocumentoUseCase` e `ResumoDocumento` em `application/resumo_documento.py`, consumindo `LLMPort`, verificando com mock que uma única chamada é feita e que os dois resumos são retornados
- [ ] 4.2 Montar o prompt com a fórmula XYZ e os limites de 280/1500, verificando com teste o conteúdo do prompt enviado
- [ ] 4.3 Truncar os resumos para 280/1500 e limitar a entrada ao orçamento máximo, verificando com testes de fronteira
- [ ] 4.4 Tratar texto vazio sem chamar a LLM e fazer parsing tolerante com fallback para resposta inteira, verificando com testes os casos vazio, formato esperado e formato inesperado
- [ ] 4.5 Propagar as exceções tipadas da `llm-core` sem conversão, verificando com testes que `LLMUnavailableError` e `LLMCommunicationError` chegam ao consumidor

## 5. Widget de Texto Somente-Leitura

- [ ] 5.1 Implementar `ReadonlyText` em `presentation/gui/widgets/readonly_text.py` com cursor visível e bloqueio de edição, verificando com testes que uma tecla de caractere não altera o conteúdo
- [ ] 5.2 Garantir Ctrl+A e Ctrl+C e a navegação por Shift+setas no `ReadonlyText`, verificando com testes que a seleção e a cópia funcionam

## 6. Painel — Visão de Agrupamento

- [ ] 6.1 Mapear os nós de agrupamento (ticker, ano, mês, categoria) no `DocumentTreePanel`, verificando com teste que um nó de agrupamento tem payload de agrupamento
- [ ] 6.2 Renderizar a lista Markdown com níveis relativos (`#` no agrupamento selecionado, incrementando nos sub-agrupamentos) e um item por documento com o `short_summary`, verificando com testes a seleção de ticker e de categoria
- [ ] 6.3 Aplicar a mensagem de indisponibilidade condicional (`Resumo indisponível.` + sufixo) conforme a LLM esteja configurada, verificando com testes os dois sufixos

## 7. Painel — Geração e Pré-visualização

- [ ] 7.1 Compor a pré-visualização do documento como `long_summary` + linha em branco + `---` + linha em branco + texto integral, verificando com teste a composição exata
- [ ] 7.2 Gerar os resumos sob demanda em thread de trabalho com estado de carregamento e persistência no store, verificando com `LLMPort` mockado que o catálogo do documento é atualizado e exibido
- [ ] 7.3 Exibir a mensagem de indisponibilidade como `long_summary` quando a LLM não está configurada ou quando a geração falha, verificando com testes os casos "não configurada" e "exceção tipada"
- [ ] 7.4 Descartar resultados obsoletos quando a seleção muda durante a geração, verificando com teste de troca de seleção concorrente

## 8. Testes e Quality Gate

- [ ] 8.1 Atualizar os testes existentes do `DocumentTreePanel` para o novo comportamento de pré-visualização e verificar que a suíte passa
- [ ] 8.2 Executar `make lint` e garantir que não há erros de linting no código novo
- [ ] 8.3 Executar `pytest -m "not llm"` e garantir que a suíte base passa sem regressão
- [ ] 8.4 Executar `openspec validate documentos-resumos` e garantir que a change permanece válida
