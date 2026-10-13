## Why

Ao acionar "Resumir pendentes" na sub-aba "Notícias", uma notícia pode ser encerrada por inatividade (timeout) do watchdog, mas o log registra apenas o id e o grupo do job ("Job 22 do grupo resumos encerrado por inatividade"), não qual notícia demorou. A causa é dupla: (1) o `JobHandle` e o watchdog não carregam nenhuma descrição do item em processamento; e (2) a resolução do documento vinculado de notícias "Geral" (requisições de rede com retentativas e parse do PDF baixado) não está sob o orçamento de extração por item e pode exceder o limite de inatividade, matando o job no meio do item — antes que os warnings por item de `preparar_texto` cheguem a registrar o nome. Sem identificar a notícia, não há como diagnosticar nem limitar o problema.

## What Changes

- O watchdog de inatividade/liveness passa a registrar, no aviso de encerramento involuntário, a descrição do item em processamento, exposta pelo worker por um novo gancho (`JobContext.descrever`) que não afeta a detecção de travamento.
- O lote de resumos (e a finalização de extração) marcam o item corrente antes de cada extração/resumo, de modo que o aviso do watchdog identifique a notícia.
- A resolução do documento vinculado de notícias "Geral" passa a ser limitada pelo mesmo orçamento de extração por item (90s, escalável em retry), cobrindo as requisições de rede e o parse do PDF baixado; ao esgotar o orçamento, a notícia permanece pendente e o evento é registrado no log nomeando o item.
- A extração de PDF passa a oferecer o caminho orçado a partir de bytes, para que o PDF baixado de um vínculo também respeite o orçamento.
- Efeito: a duração de cada notícia fica abaixo do limite de inatividade e qualquer encerramento anormal (ou estouro de orçamento) nomeia o item.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `background-jobs`: o watchdog indica a atividade/item corrente no aviso de encerramento por inatividade e por thread morta sem término.
- `noticias-panel`: a resolução do documento vinculado respeita o orçamento de extração por item e registra a notícia quando o orçamento se esgota, mantendo-a pendente.
- `extracao-texto-pdf`: a extração orçada passa a cobrir PDF a partir de bytes (documento vinculado baixado), mantendo os mesmos estados e o limite de 90 segundos.

## Impact

- `src/flowscope/presentation/gui/background/manager.py`, `job.py`, `context.py`: descritor de atividade no `JobHandle`, gancho `JobContext.descrever` e uso no log do watchdog.
- `src/flowscope/presentation/gui/resumos_job.py`, `src/flowscope/presentation/gui/finalizacao_job.py`: marcação do item corrente a cada passo.
- `src/flowscope/presentation/gui/charts/noticias_panel.py`: deadline de extração por notícia repassado ao resolvedor do vínculo.
- `src/flowscope/infrastructure/b3/noticias_vinculo.py`: respeito ao deadline nas requisições (GET/POST) e no parse do PDF baixado.
- `src/flowscope/application/extracao_orcada.py`: extração orçada de PDF a partir de bytes.
- Testes de `background`, `noticias_panel`, `noticias_vinculo` e `extracao_orcada`.
- Sem novas dependências externas.
