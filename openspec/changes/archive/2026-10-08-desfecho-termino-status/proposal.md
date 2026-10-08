## Why

Processamentos assíncronos podem encerrar sem qualquer aviso na barra de status — ou, pior, com uma mensagem de sucesso não merecida. O término do job hoje carrega apenas `cancelado: bool`, e o único aviso de interrupção depende de um token global do presenter. Uma falha fatal sem callback de erro, um job encerrado pelo watchdog ou uma exceção que escapa do worker deixam o usuário sem saber que a operação não concluiu.

## What Changes

- Introduzir um **desfecho terminal** explícito no ciclo de vida do job: `SUCESSO`, `FALHA`, `CANCELADO` e `ABORTADO`, carregado pelo evento de término.
- O desfecho é **declarado pelo worker** (que sabe se recuperou falhas) e tem default por exceção que escapa; exceção não tratada e `BaseException` resultam em `FALHA`.
- Separar **cancelamento do usuário** (`CANCELADO`) de **encerramento involuntário** pelo watchdog (`ABORTADO`), hoje ambos terminam com `cancelado=True` mas só o primeiro mostra mensagem.
- Adicionar uma **rede de segurança de status**: falha fatal que não teve callback de erro consumidor produz mensagem genérica de falha, em vez de "Pronto.".
- **BREAKING** (interno): remover a dependência do token global `presenter._cancel_token` para decidir a mensagem; o desfecho passa a ser a única autoridade.
- Corrigir a mensagem de conclusão de aquisição de documentos/notícias para não afirmar atualização quando nada foi adquirido.
- Adicionar fallback de falha na pré-visualização de documento/notícia, que hoje pode ficar presa em "Carregando…".

## Capabilities

### New Capabilities
<!-- Nenhuma: o desfecho terminal estende o mecanismo existente de background-jobs. -->

### Modified Capabilities

- `background-jobs`: o término do job DEVE publicar um desfecho terminal (`SUCESSO`/`FALHA`/`CANCELADO`/`ABORTADO`), declarado pelo worker ou derivado de exceção que escapa, e o watchdog DEVE encerrar com o desfecho de aborto.
- `process-cancellation`: o desfecho visual DEVE distinguir cancelamento do usuário de encerramento involuntário e DEVE avisar falha fatal não reportada, mantendo que cancelamento não é tratado como falha.
- `documentos-aquisicao-painel`: a mensagem de conclusão da aquisição NÃO DEVE afirmar atualização quando nada foi adquirido; zero itens adquiridos resulta em desfecho neutro.
- `noticias-panel`: a mensagem de conclusão da aquisição NÃO DEVE afirmar atualização quando nada foi adquirido, e a falha da leitura/pré-visualização DEVE sair do estado de carregamento exibindo mensagem informativa.
- `documentos-ticker-panel`: a falha da pré-visualização de um documento DEVE sair do estado de carregamento e exibir mensagem informativa, sem permanecer "Carregando…".

## Impact

- **Código (apresentação):** `presentation/gui/background/{events,job,context,manager}.py`, `app_wiring.py`, `presenter.py`, `app_actions.py`, `noticias_actions.py`, `controller_data.py`, `fundamental_job.py`, `chat/envio.py`, `charts/document_flow_mixin.py`.
- **Código (infra, opcional):** `infrastructure/b3/documentos_aquisicao.py` e `noticias_carga.py` passam a retornar contagem de itens adquiridos (mudança aditiva de retorno).
- **Testes afetados:** `test_presenter.py`, `test_cancelamento_integracao.py`, `test_startup_gate.py`, `test_carga_principal.py` e testes de painéis de documentos/notícias.
- **Sem impacto em domínio/aplicação:** o desfecho é um conceito da camada de apresentação; nenhum port ou caso de uso muda de contrato.
