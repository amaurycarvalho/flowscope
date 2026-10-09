## Context

Ver `proposal.md` — Why. A avaliação de guidance por RG já existe: `GuidanceService.avaliar` (`application/documentos/document_guidance.py:67`) devolve o `AvaliacaoGuidance` da entrada do ledger daquele RG, inclusive em cache hit (`AvaliarGuidanceUseCase.avaliar_rg`, `application/avaliar_guidance.py:56`). No fluxo de leitura, `DocumentFlowMixin._trabalhar` (`presentation/gui/charts/document_flow_mixin.py:217`) chama `avaliar_guidance` mas descarta o retorno; a composição da pré-visualização (`_mostrar_documento`, `:414`) só conhece resumo e texto. No lote, `resumos_job._resumir` (`presentation/gui/resumos_job.py:156`) também descarta o retorno e publica apenas o resumo.

O item da coluna `Informações adicionais` é formatado em `application/fundamental/linhas.py:175` (`_itens_guidance`), hoje restrito àquele contexto.

## Goals / Non-Goals

**Goals:**
- Exibir o guidance do RG selecionado entre o resumo e o `---`, com a mesma formatação da coluna Fundamentos.
- Reusar a avaliação já produzida no worker de leitura, sem I/O de ledger na thread do Tk.
- Manter a consistência do preview recomposto pelo lote de resumos.

**Non-Goals:**
- Alterar a extração/avaliação de guidance ou o formato do ledger.
- Alterar a coluna `Informações adicionais` (guidance corrente do FII).
- Exibir guidance de documentos que não sejam Relatórios Gerenciais.

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

## Risks / Trade-offs

- **[Risco] Extração parcial avaliar guidance sobre texto incompleto** → o guidance, se houver, é exibido; a extração parcial já é retentada automaticamente, e a reavaliação substitui a entrada. Aceito.
- **[Risco] Painéis sem guidance (Notícias) terem `avaliar_guidance` devolvendo `None`** → o preview do lote trata `None` como ausência de item, sem quebrar. Mitigado por teste.
- **[Trade-off] Assinatura do resultado do lote muda de `ResumoDocumento` para tupla** → atualizar o protocolo, `_aplicar_resultado_resumo` e os testes do lote no mesmo passo.

## Migration Plan

Sem migração de dados: o formato do ledger não muda. Rollback = reverter a composição e as propagação; nenhuma persistência nova.
