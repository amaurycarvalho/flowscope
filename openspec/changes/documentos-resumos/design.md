## Context

Ver `proposal.md` para a motivação. O estado atual relevante:

- `DocumentCatalog.catalogo(ticker)` varre `~/.cache/flowscope/{bdr,informe-mensal,documentos-relevantes}` e monta `CatalogoTicker` com dataclasses congeladas; `DocumentoArquivo` não tem campos de resumo.
- `DocumentTreePanel` guarda apenas nós de **arquivo** em `self._itens`; nós de pasta não têm payload. A pré-visualização usa `texto_preview()` em um `tk.Text(state=DISABLED)`.
- O projeto persiste dados derivados em JSON por ticker com escrita atômica e tolerância a corrupção (`JsonFundamentalHistoryStore`, em `~/.cache/flowscope/fundamentos/`). Não há uso de `sqlite3` em `src/` hoje.
- A change `llm-core` (planejamento concluído, ainda não implementada) fornece `LLMPort.complete()`, `create_llm_provider()`, `check_llm_deps()` e as exceções tipadas. Esta change a consome como base.

## Goals / Non-Goals

**Goals:**
- Resumos curto e longo persistidos por documento, reutilizados entre execuções.
- Visão Markdown de agrupamentos com os resumos curtos.
- Geração sob demanda do resumo longo ao abrir um documento, sem travar a GUI.
- Campo de texto somente-leitura copiável, com atalhos e cursor.
- Serviço de resumo isolado, testável com `LLMPort` mockado.

**Non-Goals:**
- Geração em lote/pré-computação de resumos de um agrupamento inteiro.
- Sumarização por map-reduce de documentos que excedam o orçamento de entrada.
- Alterar a aquisição, a varredura ou a abertura de documentos.
- Persistência do histórico de conversas (sem relação com `llm-chat`).

## Decisions

### 1. Store de resumos em JSON por ticker

**Decisão:** Persistir em `~/.cache/flowscope/document-summaries/<TICKER>.json`, um arquivo por ticker, com escrita atômica (reutilizando `_atomic_write_bytes`), versão de schema e tolerância a arquivo ausente/corrompido. A chave de cada documento é o caminho relativo à raiz de cache (ex.: `bdr/ALZR11/2026/02/10.pdf`), que é estável e globalmente único entre as raízes.

**Alternativa considerada:** arquivo global único; sidecar `<doc>.summary.json` ao lado do arquivo; tabela SQLite.
**Rejeitada porque:** o arquivo global sofre reescrita total e concorrência; o sidecar polui os diretórios de cache gerenciados pelas changes de extração; SQLite contraria o padrão atual do projeto (JSON atômico) e adiciona complexidade sem necessidade nesta escala. O JSON por ticker carrega todos os resumos de um ticker em uma leitura, exatamente o que a visão de agrupamento precisa.

### 2. Campos de resumo no catálogo, preenchidos na consulta

**Decisão:** adicionar `short_summary: str | None = None` e `long_summary: str | None = None` a `DocumentoArquivo` (frozen) e enriquecer cada entrada em `DocumentCatalog.catalogo()` a partir do store injetado. `None` significa "não gerado"; string vazia fica reservada a um resumo gerado vazio.

**Alternativa considerada:** usar `""` como padrão.
**Rejeitada porque:** `""` é ambíguo entre "não gerado" e "gerado sem conteúdo", e a regra de exibição precisa distinguir os dois.

### 3. Serviço de resumo em `application/`

**Decisão:** `application/resumo_documento.py` com `ResumirDocumentoUseCase(llm: LLMPort)` e `resumir(texto) -> ResumoDocumento(short_summary, long_summary)`. Uma única chamada de completion pedindo os dois resumos; prompt com a fórmula XYZ e os limites; parsing tolerante de um formato delimitado (ex.: `CURTO:` / `LONGO:`); fallback usando a resposta inteira como longo e os primeiros 280 como curto; truncamento para 280/1500; entrada limitada a um orçamento (ex.: 12.000 caracteres).

**Alternativa considerada:** duas chamadas separadas (uma por resumo).
**Rejeitada porque:** dobra o consumo de cota/latência sob RPM 5 e o resultado é o mesmo; uma chamada com saída estruturada é mais econômica e o parsing tolerante cobre formatos inesperados.

### 4. Visão Markdown do agrupamento com níveis relativos

**Decisão:** o nó selecionado é o cabeçalho `#` e cada sub-agrupamento incrementa o nível. Ex.: selecionar o ticker gera `# ALZR11`, `## 2026`, `### 02`, `#### Informe Mensal`, `- 123.html — <short_summary>`. Cada item é um bullet com o nome do arquivo e o `short_summary` (ou a mensagem de indisponibilidade).

**Alternativa considerada:** níveis absolutos por profundidade (ticker sempre `#`, ano `##`, ...).
**Rejeitada porque:** a regra pede que o agrupamento selecionado seja o topo da lista; níveis relativos mantêm a lista legível em qualquer profundidade.

**Consequências:** o painel precisa mapear cada nó a um contexto de agrupamento (nível + chave) e reconstruir a subárvore a partir do `CatalogoTicker` para renderizar a lista.

### 5. "Configurada e funcional" = provedor ativo + dependências

**Decisão:** considerar a LLM utilizável quando `llm.chat.provider != "none"` e as dependências `[llm]` estão presentes. Falhas reais durante a geração (timeout, provedor, cota, configuração) caem na mesma mensagem de indisponibilidade.

**Alternativa considerada:** exigir um teste de conexão bem-sucedido persistido antes de habilitar a geração.
**Rejeitada porque:** adiciona estado e uma etapa manual sem mudar a mensagem final; a mensagem de indisponibilidade já cobre tanto "não configurada" quanto "falhou".

### 6. Geração assíncrona com descarte de resultado obsoleto

**Decisão:** ao selecionar um documento sem `long_summary`, o painel inicia a extração do texto e, em seguida, a chamada de resumo em thread de trabalho, publicando o desfecho na thread do Tk por fila (padrão já usado no painel). Um identificador de requisição descarta resultados de seleções anteriores; um estado "Gerando resumo…" é exibido durante a chamada. Em sucesso, os resumos são gravados no store e a pré-visualização composta é exibida.

**Alternativa considerada:** geração síncrona na thread da interface.
**Rejeitada porque:** o rate limiter da `llm-core` pode bloquear e a rede demora, congelando a janela.

### 7. Widget de texto somente-leitura navegável

**Decisão:** extrair um widget `ReadonlyText` (subclasse de `tk.Text`) que permanece com `state=NORMAL` para permitir cursor e seleção, mas intercepta `<Key>` e bloqueia toda tecla que alteraria o conteúdo (caracteres, Return, BackSpace, Delete, colar), deixando passar navegação, Shift+setas, Home/End/Page e Ctrl+A/Ctrl+C. `insertwidth` garante o cursor visível. O painel passa a usar esse widget no lugar do `tk.Text` com `state=DISABLED`.

**Alternativa considerada:** manter `state=DISABLED` e bindar apenas Ctrl+A/Ctrl+C.
**Rejeitada porque:** widget desabilitado não exibe cursor nem responde a Shift+setas, contrariando o requisito.

### 8. Layout de módulos

```
application/resumo_documento.py        ResumirDocumentoUseCase, ResumoDocumento
infrastructure/document_summaries.py   JsonDocumentSummaryStore (load/save por ticker)
infrastructure/document_catalog.py     DocumentoArquivo + campos; catalogo() enriquece
presentation/gui/widgets/readonly_text.py   ReadonlyText
presentation/gui/charts/document_tree_panel.py  visão de agrupamento + geração
```

**Decisão:** o store é infraestrutura; o serviço é aplicação; o widget é apresentação.
**Alternativa considerada:** colocar o store dentro de `document_catalog.py`.
**Rejeitada porque:** separa a varredura (somente leitura) da persistência (leitura/escrita) e facilita testar cada um isoladamente.

## Risks / Trade-offs

- **[Risco] documentos longos excedem a janela de contexto** → Mitigação: orçamento máximo de entrada com truncamento; map-reduce fica para uma evolução futura.
- **[Risco] custo e latência na primeira abertura de cada documento** → Mitigação: persistência por documento (reabrir é grátis) e rate limiter da `llm-core`; a geração é assíncrona e com estado de carregamento.
- **[Risco] resultado de resumo chegar após o usuário trocar de seleção** → Mitigação: identificador de requisição que descarta resultados obsoletos.
- **[Risco] arquivo JSON de resumos corrompido** → Mitigação: leitura tolerante (trata como vazio) e escrita atômica, no padrão do `JsonFundamentalHistoryStore`.
- **[Trade-off] resumos não são pré-gerados** → o usuário só vê resumos curtos no agrupamento depois de abrir cada documento; é o comportamento pedido na regra 2.2.
- **[Trade-off] mensagem de indisponibilidade não é persistida** → evita gravar estado derivado de falha; a próxima abertura tenta de novo.

## Migration Plan

1. Confirmar que a change `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `check_llm_deps`, exceções).
2. Implementar `JsonDocumentSummaryStore` e os campos do catálogo, com testes.
3. Implementar `ResumirDocumentoUseCase` com `LLMPort` mockado, com testes.
4. Implementar o `ReadonlyText` e os testes de comportamento.
5. Integrar no `DocumentTreePanel`: visão de agrupamento, geração assíncrona e composição da pré-visualização.
6. Atualizar os testes existentes do painel para o novo comportamento.

**Rollback:** remover o diretório `~/.cache/flowscope/document-summaries/` e o uso do serviço restaura a pré-visualização anterior; nenhuma migração de dados é necessária.
