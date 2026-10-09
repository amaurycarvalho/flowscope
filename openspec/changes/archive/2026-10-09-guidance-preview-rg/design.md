## Context

Ver `proposal.md` — Why. A avaliação de guidance por RG já existe: `GuidanceService.avaliar` (`application/documentos/document_guidance.py:67`) devolve o `AvaliacaoGuidance` da entrada do ledger daquele RG, inclusive em cache hit (`AvaliarGuidanceUseCase.avaliar_rg`, `application/avaliar_guidance.py:56`). No fluxo de leitura, `DocumentFlowMixin._trabalhar` (`presentation/gui/charts/document_flow_mixin.py:217`) chama `avaliar_guidance` mas descarta o retorno; a composição da pré-visualização (`_mostrar_documento`, `:414`) só conhece resumo e texto. No lote, `resumos_job._resumir` (`presentation/gui/resumos_job.py:156`) também descarta o retorno e publica apenas o resumo.

O item da coluna `Informações adicionais` é formatado em `application/fundamental/linhas.py:175` (`_itens_guidance`), hoje restrito àquele contexto.

O botão "Resumir pendentes" (`resumir_habilitado`, `presentation/gui/charts/document_flow_mixin.py:57`) e o alvo do lote (`app_resumos_actions._resumir_documentos_pendentes`) usam apenas `documentos_sem_resumo()` (`:47`), isto é, documentos com `long_summary is None`. Um RG já resumido, mas cuja entrada no ledger esteja ausente ou marcada como `deterministico` enquanto a IA está ativa, não aparece nessa lista: o botão pode permanecer desabilitado e o lote nunca o avalia, ainda que `AvaliarGuidanceUseCase.avaliar_rg` (`application/avaliar_guidance.py:56`) já saiba promovê-lo a `ia`. O ledger (`JsonGuidanceStore.obter_avaliacao`, `infrastructure/guidance_store.py:59`) lê o JSON do ticker a cada consulta, sem memoização, então a verificação de pendências não deve ocorrer na thread do Tk.

## Goals / Non-Goals

**Goals:**
- Exibir o guidance do RG selecionado entre o resumo e o `---`, com a mesma formatação da coluna Fundamentos.
- Reusar a avaliação já produzida no worker de leitura, sem I/O de ledger na thread do Tk.
- Manter a consistência do preview recomposto pelo lote de resumos.
- Habilitar o botão "Resumir pendentes", com IA ativa, quando houver Relatórios Gerenciais já resumidos pendentes de avaliação de guidance, e fazer o lote avaliá-los.

**Non-Goals:**
- Alterar a extração/avaliação de guidance ou o formato do ledger.
- Alterar a coluna `Informações adicionais` (guidance corrente do FII).
- Exibir guidance de documentos que não sejam Relatórios Gerenciais.
- Avaliar guidance pela IA quando a IA não estiver configurada (o determinístico continua restrito ao caminho de resumo pendente).

## Decisions

### 1. Orientar a exibição pela avaliação por RG, não pelo guidance corrente

Usar o `AvaliacaoGuidance` devolvido por `GuidanceService.avaliar` (chave de conteúdo do documento). Alternativa: usar `GuidanceStore.obter(ticker)` (guidance corrente). Rejeitada: o requisito é exibir o guidance do RG lido, que pode divergir do corrente quando o usuário abre um RG anterior; o corrente já aparece em Fundamentos.

### 2. Propagar a avaliação pelo resultado do worker de leitura

`_trabalhar` captura o retorno de `avaliar_guidance` e inclui no `ctx.resultado(valor=(resultado, precisa, resumo, avaliacao))`; `_aplicar_preview` recebe a avaliação e a converte em texto de guidance. Alternativa: ler o ledger em `_aplicar_preview` (thread do Tk). Rejeitada: viola a regra de não fazer I/O de cache na thread da interface (`documentos-ticker-panel`), e o dado já está disponível no worker.

### 3. Formatter compartilhado em `application/fundamental/linhas.py`

Extrair `formatar_guidance(guidance: Guidance) -> str` de `_itens_guidance` e reusá-lo na coluna e na pré-visualização. Alternativa: duplicar o formato na apresentação. Rejeitada: a divergência entre os dois textos é exatamente o que o requisito quer evitar. A apresentação já importa de `application.*`, respeitando as fronteiras.

### 4. Composição com lista de partes em `_mostrar_documento`

Assinar `_mostrar_documento(texto, long_summary, anotacao=None, guidance_texto=None)` e montar `partes = [long_summary, guidance_texto]` (presentes), produzindo `"{'\n\n'.join(partes)}\n\n---\n\n{corpo}"`, ou `corpo` quando não há partes. Isso posiciona o guidance antes do `---`, com linha em branco antes e depois, e cobre o caso sem resumo (guidance imediatamente antes do `---`).

### 5. Lote propaga `(resumo, avaliacao)`

`DocumentFlowMixin.avaliar_guidance` passa a devolver `AvaliacaoGuidance | None`; `resumos_job._resumir` publica `ctx.resultado(valor=(resumo, avaliacao), dados=arquivo)`; `app_resumos_actions._aplicar_resultado_resumo` desempacota e repassa ao painel (`refletir_resumo`/`aplicar_resumo`), que repassa ao `_mostrar_documento`. O protocolo `_PainelDocumentos.avaliar_guidance` em `resumos_job.py` é ajustado para o novo retorno. Alternativa: não cobrir o lote nesta iteração. Rejeitada: deixaria o preview inconsistente entre a leitura e o lote sem motivo técnico.

### 6. Definir "pendente de guidance" pelo método da entrada do ledger

Um RG (categoria `Relatorio`) é considerado pendente de guidance quando `GuidanceStore.obter_avaliacao(ticker, chave)` devolve `None` ou uma avaliação com `metodo != METODO_IA`, e a IA está ativa. Isso espelha exatamente o portão de `AvaliarGuidanceUseCase.avaliar_rg`: entradas `ia` são ignoradas; entradas `deterministico` (ou ausentes) são (re)avaliadas pela IA. Alternativa: considerar pendente apenas a ausência de entrada. Rejeitada: deixaria entradas determinísticas antigas permanentemente sem promoção pela IA, contrariando o requisito de a IA prevalecer. A pertinência a FII é dada pela própria categoria `Relatorio` (Relatório Gerencial, documento de FII), não por `classificar_ticker`: o painel não recebe a taxonomia/resolvedor `code-cvm-resolution`, e a classificação sintática sem eles devolve `DESCONHECIDO` para FIIs como `ALZR11` e `GGRC11`. O `GuidanceService.pendentes` filtra pela categoria, que é o sinal confiável disponível.

### 7. Calcular a pendência no worker de leitura do catálogo

O conjunto de RGs pendentes é derivado por um método do `GuidanceService` que consulta o ledger, e é computado no mesmo worker que hoje lê o catálogo (`DocumentTreePanel.carregar_catalogo`, acionado por `app_actions._submeter_leitura_documentos`). O worker devolve o catálogo junto das chaves/caminhos pendentes; a thread do Tk apenas guarda o conjunto e `resumir_habilitado` continua sendo uma decisão pura sobre estado em memória. Alternativa: consultar o ledger dentro de `resumir_habilitado` (thread do Tk). Rejeitada: `JsonGuidanceStore.obter_avaliacao` faz I/O de arquivo por consulta, violando a regra de não ler cache na thread da interface.

### 8. Lote com união de pendentes e recomposição sem novo resumo

`_resumir_documentos_pendentes` passa a mirar a união de `documentos_sem_resumo()` com os RGs pendentes de guidance (FII, IA ativa). Para os RGs já resumidos, `gerar_resumo_estrito` devolve `None` (não há resumo a gerar) e apenas a avaliação de guidance executa, reaproveitando os resumos e o texto em cache via `GuidanceService.avaliar`. `app_resumos_actions._aplicar_resultado_resumo` passa a recompor a pré-visualização quando houver `avaliacao` mesmo com `resumo=None`, reutilizando o `long_summary` vigente do documento. Alternativa: fase dedicada só para guidance. Rejeitada: duplicaria a orquestração de progresso/cancelamento sem ganho, já que a fase de resumo já é um no-op para esses itens.

## Risks / Trade-offs

- **[Risco] Extração parcial avaliar guidance sobre texto incompleto** → o guidance, se houver, é exibido; a extração parcial já é retentada automaticamente, e a reavaliação substitui a entrada. Aceito.
- **[Risco] Painéis sem guidance (Notícias) terem `avaliar_guidance` devolvendo `None`** → o preview do lote trata `None` como ausência de item, sem quebrar. Mitigado por teste.
- **[Trade-off] Assinatura do resultado do lote muda de `ResumoDocumento` para tupla** → atualizar o protocolo, `_aplicar_resultado_resumo` e os testes do lote no mesmo passo.
- **[Risco] Pendência de guidance sem fontes avaliáveis deixaria o botão habilitado indefinidamente** → o conjunto de RGs pendentes considera apenas documentos já com `long_summary`, que sempre fornece ao menos uma fonte à cascata; documentos sem resumo seguem o caminho de resumo já existente.
- **[Risco] Leitura do ledger no worker de catálogo a cada troca de ticker** → aceitável: uma leitura do JSON do ticker por carga, já fora da thread do Tk; o conjunto é vazio quando não há `GuidanceService` ou a IA está inativa.

## Migration Plan

Sem migração de dados: o formato do ledger não muda. Rollback = reverter a composição e as propagação; nenhuma persistência nova.
