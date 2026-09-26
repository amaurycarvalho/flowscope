## Context

Ver `proposal.md` — Why. Hoje `ResumosPendentesJob` roda em uma thread de trabalho e publica `(RESULTADO, arquivo, resumo)` em uma fila; a thread do Tk drena essa fila em `_poll_resumos_job` e só então chama `painel.aplicar_resumo`, que grava no `JsonDocumentSummaryStore`. Logo a gravação fica a reboque do Tk: no cancelamento `_poll_resumos_job` finaliza sem drenar (`app_resumos_actions.py:110`) e um fechamento deixa na fila tudo o que foi gerado e ainda não aplicado. A store faz *read-modify-write* do JSON inteiro por ticker (`document_summaries.py:68`).

Restrição relevante: a árvore continua clicável durante o lote (só os botões são bloqueados — `app_status.py:201`), então a pré-visualização individual pode gravar resumos ao mesmo tempo que o lote.

## Goals / Non-Goals

**Goals:**
- Garantir que cada resumo gerado esteja no disco antes de o lote seguir para o próximo documento.
- Tornar a gravação resistente a concorrência entre o lote e a pré-visualização.
- Manter o comportamento observável atual (fases, progresso, desfecho, ordem dos documentos) inalterado.

**Non-Goals:**
- Alterar a ordem de processamento dos documentos (ver `noticias-resumo-lote-ordenado` para o caso das notícias).
- Trocar o formato de persistência ou migrar dados.
- Persistir resumos parciais da LLM (um resumo só é gravado quando completo).

## Decisions

### 1. Gravar no worker, não drenar a fila no Tk

Cada resumo é gravado na thread de trabalho imediatamente após a geração; a fila passa a servir apenas para atualizar a interface. Isso cobre cancelamento, fechamento e crash de uma vez, em vez de apenas o caminho de cancelamento.

Alternativa considerada: drenar a fila antes de finalizar no cancelamento — descartada por não cobrir fechamento/crash e por ainda depender da thread do Tk.

### 2. Seam no fluxo compartilhado, sem bifurcar o job

`ResumosPendentesJob` e `DocumentFlowMixin` são compartilhados entre Documentos e Notícias. Em vez de duplicar o job, a fachada do painel ganha um gancho (ex.: `persistir_no_lote`/um método de "gerar e persistir") que o job consulta. Este change liga o gancho para Documentos; `noticias-resumo-lote-ordenado` o reutiliza.

Alternativa considerada: um job só para notícias — descartada por duplicar a lógica de fases e progresso.

### 3. Separar "gravar" (worker) de "refletir" (Tk)

O caminho do worker pode apenas escrever no store e devolver o `DocumentoArquivo` atualizado; ele NÃO DEVE tocar em `_itens`, `_por_caminho`, `_preview_cache` nem em widgets. A thread do Tk deixa de regravar e passa a apenas refletir em memória e na pré-visualização. Isso mantém a regra de thread-safety do Tk intacta.

### 4. Store segura a escritas concorrentes

`JsonDocumentSummaryStore.salvar` passa a serializar o *read-modify-write* com um `threading.Lock`, preservando os resumos já gravados. A escrita atômica (temp + rename) já existe; o lock resolve o *lost update*.

Alternativa considerada: fila de escrita dedicada — mais complexa e desnecessária para o volume.

### 5. Manter as duas fases

A fase de preparação continua preparando todos os textos antes de resumir. A garantia de persistência vale para os resumos na fase 2 (o cache de texto já era gravado por item em `preparar_texto`).

## Risks / Trade-offs

- [Chamada de store no worker cruzar com a pré-visualização] → lock no `salvar`; nenhum widget é tocado no worker.
- [Regressão no fluxo de aplicação no Tk] → a aplicação passa a ser só de memória; testes de estado do botão e de descarte por troca de ticker devem continuar passando.
- [Ordem de implementação com as notícias] → este change introduz o seam; a change das notícias depende dele e deve vir depois.

## Migration Plan

1. Adicionar o lock à store e os testes de concorrência.
2. Introduzir o gancho de persistência no worker e ajustar o job e a aplicação no Tk.
3. Ligar o gancho para Documentos e validar o desfecho e o cancelamento.
