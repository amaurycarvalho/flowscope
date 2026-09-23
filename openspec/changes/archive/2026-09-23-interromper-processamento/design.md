## Context

Ver `proposal.md` — Why para a motivação e a spec `process-cancellation` para o contrato de comportamento.

O sistema já possui três jobs assíncronos com o mesmo padrão (thread de trabalho + fila + drenagem na thread do Tk): `FundamentalJob`, `DocumentosJob` e `ResumosPendentesJob`. Todos já têm guardas de identidade/geração para descartar mensagens tardias e um watchdog de inatividade de 120s que encerra jobs travados. O `FlowScopePresenter` é a autoridade única do estado ocupado (`_operacoes_ativas`), da barra de progresso e da restauração de controles/cursor.

A carga principal (`on_index_clicked`/`on_load_data`) roda **síncrona na thread do Tk** e não é coberta — está fora do escopo e será migrada em change própria.

## Goals / Non-Goals

**Goals:**
- Botão de interromper na barra de status, com ciclo de vida acoplado apenas a jobs canceláveis.
- Cancelamento cooperativo real de todos os jobs em background, sem confundir com falha.
- Finalização imediata da UI e mensagem "Processamento interrompido.".
- Token reiniciado por nova operação, sem afetar operações futuras.

**Non-Goals:**
- Migrar a carga principal síncrona para thread (change futura).
- Interromper a chamada de rede bloqueante no meio (`requests.get`), ou cancelar no meio da análise de um ticker.
- Desfazer itens já persistidos em cache (documentos/resumos) ou no histórico fundamentalista.
- Cancelamento individual por job (o clique cancela tudo).

## Decisions

### Decisão 1: token de cancelamento no presente, limpo na transição ocioso → ocupado
O `FlowScopePresenter` passa a ser dono de um `threading.Event` (`_cancel_token`) e de um contador `_jobs_cancelaveis`. `enter()` limpa o token somente na transição 0→1; `exit()` na transição →0 finaliza e, se o token estiver setado, publica "Processamento interrompido.".
- **Por quê**: centraliza a semântica onde já vive a autoridade do estado ocupado; evita dispersão.
- **Alternativas**: token global de módulo (difícil de testar/resetar) ou na `FlowScopeGUI` (duplica autoridade). Descartadas.

### Decisão 2: cancelamento cooperativo via token explícito + exceção dedicada
Novo módulo `src/flowscope/application/cancellation.py` com `OperacaoCancelada` e o token. Os laços de trabalho checam o token **no topo de cada iteração**, fora dos `try` tolerantes de erro, e lançam `OperacaoCancelada`. Os jobs recebem o token e o tratam separadamente de erro.
- **Por quê**: o `FundamentalAnalysisUseCase` envolve o `progress_callback` de sucesso no `try/except Exception` por ticker (fundamental_analysis.py:148-162); uma exceção lançada de dentro do callback seria engolida como falha recuperável e o laço continuaria.
- **Alternativas**: fazer o `progress_callback` lançar (menos invasivo em assinaturas, mas frágil pelos `try` que engolem, exigindo correções de re-raise de qualquer forma). Descartada.
- O módulo fica em `application` porque infraestrutura já importa de `application` (precedente: `infrastructure/b3/repository.py` importa `application.ports`).

### Decisão 3: visibilidade do botão desacoplada da barra de progresso
`_set_progress` continua controlando a barra; um novo `set_cancellable(bool)` controla o botão. O botão é mostrado/ocultado conforme `_jobs_cancelaveis`.
- **Por quê**: a barra também aparece na carga síncrona, onde o botão ficaria inerte (o Tk não processa cliques durante `update_idletasks()`).
- **Alternativas**: acoplar botão e barra (viola "botão ausente na carga síncrona"). Descartada.
- Posição: empacotado em `side=RIGHT` imediatamente antes da barra, ficando à esquerda dela.

### Decisão 4: finalização imediata da UI ao cancelar
Ao detectar o token setado, a drenagem finaliza a UI no próximo tick, sem aguardar o terminal do worker. A thread daemon encerra cooperativamente em segundo plano.
- **Por quê**: responsividade e atendimento ao requisito de o botão/barra sumirem quando o usuário interrompe; esperar poderia levar 30–60s (timeout de rede).
- **Alternativas**: aguardar o worker publicar o terminal (UI presa, pior UX). Descartada.
- As guardas de identidade (`_documentos_job is job`, `_resumos_job is job`, `generation` do fundamental) impedem que mensagens tardias da thread abandonada pintem a UI.

### Decisão 5: desfecho e supressão de sucesso centralizados
A mensagem "Processamento interrompido." é publicada em `presenter.exit()` na transição para ocioso; cada finalizador consulta o token para não exibir flash de sucesso.
- **Por quê**: com cancelar-tudo e jobs sobrepostos, evita múltiplas mensagens concorrentes.
- O flag existente `_resumos_interrompido` (app_resumos_actions.py:54) é estendido para cobrir cancelamento.

### Decisão 6: tratamento distinto de cancelamento em cada job
- `FundamentalJob._executar`: `except OperacaoCancelada` antes do `except Exception`, sem publicar `MENSAGEM_ERRO` nem logar como falha.
- `DocumentosJob._executar`: `except OperacaoCancelada: pass` antes do `except Exception`, sem warning.
- `ResumosPendentesJob._executar`: `except OperacaoCancelada` para não vazar no excepthook da thread.

## Risks / Trade-offs

- **Granularidade grossa (por ticker/documento)** → cancelar não interrompe no meio de um item; aceito como v1. Mitigação futura: aprofundar o token nos providers (follow-up).
- **Chamadas de rede bloqueantes (30–60s)** → a thread pode demorar a morrer após o clique. Mitigado pela finalização imediata da UI; thread é daemon e o processo encerra com segurança.
- **Cache/estado parcial** → documentos e resumos já persistidos permanecem (idempotente); o resultado parcial da análise fundamentalista é descartado.
- **Mensagem tardia de thread abandonada** → guardas por identidade de job e geração já existentes; a drenagem para de consumir a fila ao finalizar.
- **Cancelamento tratado como falha recuperável** → mitigado pela checagem no topo do laço (fora do `try`) e pelo tratamento dedicado nos jobs.
- **Confundir cancelamento com erro no relatório** → `houve_falha_recuperavel` não deve ser marcado no caminho de cancelamento.

## Migration Plan

- Mudança aditiva, sem migração de dados; nenhuma alteração de formato de cache ou de arquivo de preferências.
- Rollback: reverter os arquivos tocados; os watchdogs existentes continuam como rede de segurança.
- Sem novas dependências externas (`threading.Event` da biblioteca padrão).

## Open Questions

- Texto do tooltip do botão e rótulo acessível podem ser definidos na implementação sem alterar a abordagem.
