## 1. Store de texto por documento (infraestrutura)

- [x] 1.1 Implementar `JsonDocumentTextStore` em `src/flowscope/infrastructure/document_texts.py` gravando `~/.cache/flowscope/document-texts/<TICKER>.json` com o mapa `chave_documento → texto`, escrita atômica (`_atomic_write_bytes`), `schema_version` e tolerância a ausência/corrupção (modelo de `infrastructure/document_summaries.py`); verificar com testes de leitura vazia, gravação/recuperação, JSON corrompido e preservação dos demais documentos do ticker
- [x] 1.2 Reutilizar `chave_documento(caminho, base)` para a chave do documento; verificar com teste que a chave do texto coincide com a chave usada pelos resumos

## 2. Predicado de texto (aplicação/apresentação)

- [x] 2.1 Definir a porta do store de texto em `src/flowscope/application/` com o contrato de leitura/gravação por ticker; verificar que o tipo é consumível sem importar infraestrutura
- [x] 2.2 Adicionar `tem_texto(texto)` em `src/flowscope/presentation/gui/charts/document_preview.py`, retornando `False` para vazio, só espaços e para `SEM_TEXTO`; verificar com teste dos três casos

## 3. Pré-visualização ciente do cache

- [x] 3.1 Integrar o store ao fluxo `_iniciar_preview`/`_trabalhar`/`_aplicar_preview` de `charts/document_tree_panel.py`: em *hit* usar o texto do cache sem reconverter; em *miss* converter, gravar `texto` (ou `SEM_TEXTO` quando vazio) e exibir; verificar com teste de *hit* (conversão não chamada) e de *miss* (conversão chamada e texto gravado)
- [x] 3.2 Substituir `bool(texto.strip())` por `tem_texto(texto)` em `DocumentSummaryService.precisa_resumo`/`resumo_para_exibir` (`charts/document_summary.py`) e em `_mostrar_documento`; verificar com teste que, sem texto, a LLM não é chamada, nenhum resumo é persistido e o marcador é exibido
- [x] 3.3 Garantir que a abertura do documento (botão "Abrir documento", duplo clique e Enter) permanece funcional sem texto extraível; verificar com teste de abertura sobre documento sem texto
- [x] 3.4 Injetar o store no `DocumentTreePanel`/`DocumentCatalog` conforme o wiring existente; verificar que a composição do painel monta sem erro

## 4. Barra de rolagem vertical

- [x] 4.1 Empacotar a `ttk.Scrollbar` **antes** do conteúdo em `charts/document_tree_view.py` (árvore) e em `DocumentTreePanel._build_preview` (campo de texto); verificar com teste de GUI (requer `DISPLAY`) que ambas estão mapeadas (`winfo_ismapped()`) e com largura maior que zero, inclusive com o painel mais estreito que a largura requisitada do conteúdo
- [x] 4.2 Vincular a roda do mouse (`<MouseWheel>`, `<Button-4>`, `<Button-5>`) na árvore e no campo de texto, no padrão de `FundamentalTablePanel._vincular_roda`; verificar com teste de GUI que a roda rola o conteúdo

## 5. Reconhecimento do cache pela change de guidance

- [x] 5.1 Atualizar `openspec/changes/fii-guidance-informacoes-adicionais/proposal.md`, `design.md`, `specs/relatorio-gerencial-guidance/spec.md` e `tasks.md` para consumir o texto deste cache (sem reextrair) e não avaliar guidance quando `not tem_texto(texto)`, declarando a dependência desta change; verificar com `openspec validate "fii-guidance-informacoes-adicionais"`

## 6. Verificação final

- [x] 6.1 Rodar `make lint` e corrigir avisos introduzidos
- [x] 6.2 Rodar `make test` e garantir a cobertura mínima do projeto
- [x] 6.3 Validar a change com `openspec validate "cache-texto-documentos"` e `openspec validate "cache-texto-documentos" --strict`
