## Context

O lote "Resumir pendentes" já separa extração conclusiva (`OK`) de não conclusiva (`PARCIAL`, `FALHA`, `PROTEGIDO`) em `_texto_utilizavel` (`src/flowscope/presentation/gui/resumos_job.py`), mas descarta essa classificação: o job devolve apenas a contagem "sem texto" e o item permanece pendente para sempre. A apresentação já tem rota manual de senha (`DocumentFlowMixin._tentar_senha`, `_solicitar_senha` em cada painel) e o desfecho do lote é montado em `_finalizar_resumos_job` (`src/flowscope/presentation/gui/app_resumos_actions.py`), que também agenda a remontagem via `after(0, _recarregar_painel_resumos)`.

Ver `proposal.md` — Why. As regras de comportamento estão nas specs da change.

## Goals / Non-Goals

**Goals:**
- Permitir encerrar o ciclo dos itens não conclusivos, aceitando o texto parcial/falha/proteção como definitivo.
- Fazer a limitação aparecer nos resumos, presente e futuros, sem depender de reextração.
- Manter o lote não-bloqueante e a thread do Tk responsiva.

**Non-Goals:**
- Não alterar a classificação da extração em si (`extracao-texto-pdf`) nem a fórmula de resumo (`documento-summary`).
- Não finalizar automaticamente: sempre depende da confirmação do usuário.
- Não incluir ausência definitiva (`SEM_TEXTO`) nem apontador de notícia não resolvido.
- Não persistir a senha.

## Decisions

### D1. Nota embutida no texto persistido (vs. registro de finalização à parte)

Ao marcar como definitivo, o texto persistido passa a ser: `PARCIAL` → texto parcial + nota; `FALHA`/`PROTEGIDO` → apenas a nota. Assim o cache-hit de `preparar_texto` impede a reextração, o preview já mostra a nota e resumos futuros a encontram no próprio texto.

- Alternativa descartada: registrar a finalização num store paralelo e manter o cache puro. Preservaria o invariante "conteúdo = texto original", mas exigiria novo store/porta, tratamento de shards nas notícias e consulta ao registro em `preparar_texto` e na decisão de pendência — mais superfície para o mesmo resultado.
- Consequência aceita: a `documento-texto-cache` ganha uma exceção explícita (ver delta); a nota passa a ser visível ao índice do chat e à extração determinística de guidance.

### D2. Resumo determinístico para `FALHA` e `PROTEGIDO`; LLM para `PARCIAL`

Sem texto não há o que resumir: uma mensagem fixa, terminando em pontuação final (para contar como `resumo_completo`), evita custo e alucinação. O `PARCIAL` tem texto real e usa a LLM sobre `texto + nota`.

- Alternativa descartada: mandar só a nota à LLM; gasta chamada para um resumo que não resume e arrisca invenção de conteúdo.

### D3. Retry mira apenas a lista; pré-coleta de senha (vs. prompt no meio do lote)

O conjunto não conclusivo é capturado no término e o retry reprocessa exatamente esses itens. Para os `PROTEGIDO`, a senha é pré-coletada na thread do Tk (reusando `_solicitar_senha` e `MAX_TENTATIVAS_SENHA`) e passada ao lote como mapa `{caminho: senha}`, mantendo o worker não-interativo.

- Alternativa descartada: prompt just-in-time (worker→Tk→worker), que exigiria request/response novo no `BackgroundManager`.

### D4. Contrato do job devolve a classificação

`executar_resumos` deixa de devolver `int` e passa a devolver um resultado com os conjuntos `parciais`, `falhas` e `protegidos` (além de `sem_texto`). A categorização sai de `_texto_utilizavel`, que passa a expor o motivo em vez de um booleano. O desfecho padrão do lote continua sendo exibido; a confirmação usa os conjuntos.

### D5. Finalização roda como job de background

Marcar como definitivo tem chamada LLM no `PARCIAL`, então roda em job, gravando texto e resumo por item (à prova de interrupção, como o lote). O caminho determinístico não chama LLM. A thread do Tk só orquestra e reflete.

### D6. Confirmação só em término normal, após a remontagem

A confirmação é exibida em `_finalizar_resumos_job` apenas quando o lote não foi cancelado, não foi interrompido por erro, não foi abortado por cota e o escopo não mudou. Para não correr com `_itens`, a pergunta é encadeada após a remontagem agendada.

### D7. Lote/painel como seam da finalização

A finalização reusa `preparar_texto`/`gerar_e_persistir` e um novo gancho de persistência do texto definitivo (monta a nota). A montagem da nota é uma regra pura (texto a partir de status + páginas com falha), separada para teste headless. As specs de `documento-summary` e `extracao-texto-pdf` não mudam: a nota e o resumo determinístico pertencem à `finalizacao-extracao-definitiva`.

## Risks / Trade-offs

- [Nota vaza para índice do chat e regex de guidance] → A nota é claramente delimitada e informativa; a extração determinística de guidance é tolerante a texto adicional.
- [Loop de retry indefinido] → Controlado pelo usuário a cada ciclo; a cada confirmação ele pode encerrar ou finalizar.
- [Corrida entre diálogo e remontagem] → Encadear a pergunta após a remontagem concluir (efeito `after`), não disparar imediatamente.
- [Resumo determinístico não ser considerado íntegro] → Garantir pontuação final na mensagem fixa; testar `resumo_completo`.
- [Mudança do retorno de `executar_resumos` quebra testes] → Ajustar job e testes do lote junto; manter o desfecho textual equivalente.
- [Protegido sem senha multiplica prompts] → Pré-coleta por item com limite de tentativas; item sem senha permanece pendente e reclama no ciclo seguinte.

## Migration Plan

Sem migração de formato: o texto definitivo é gravado como string no cache já existente (`str -> str`), com leitura tolerante. Rollback: limpar as entradas de cache afetadas (ou o marcador de ausência) faz o item voltar a ser pendente; nenhuma estrutura nova é introduzida.

## Open Questions

- Texto exato das notas (parcial/falha/protegido) e do resumo determinístico — ajustável sem impactar specs ou abordagem.
- Se a contagem de não conclusivos deve também aparecer no desfecho padrão do lote (além da confirmação) — decisão de UI menor.
