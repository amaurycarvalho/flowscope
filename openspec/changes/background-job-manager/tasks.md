## 1. Estrutura e contrato base

- [x] 1.1 Criar o pacote `src/flowscope/presentation/gui/background/` com `job.py`, `context.py`, `scheduler.py`, `pump.py`, `manager.py` e `events.py`, e verificar que os módulos importam sem erro (`python -c "import flowscope.presentation.gui.background.manager"`)
- [x] 1.2 Definir os eventos tipados (`Progresso`, `Resultado`, `Erro`, `Termino`), o `JobHandle` (id, grupo, política, estado) e o `JobContext` (progress/emit/resultado/erro/token/cancelled) e verificar com teste unitário que o contexto não expõe widgets
- [x] 1.3 Adicionar teste de fronteira garantindo que `background/` não importa `flowscope.infrastructure`, e verificar que o guardrail de `layer-boundaries` permanece verde
- [x] 1.4 Definir os testes do manager/políticas/token/pump/watchdog em módulo headless (sem `DISPLAY` e sem `tk.Tk`) e verificar que nenhum teste novo do pacote usa `@needs_display`

## 2. Agendador e políticas

- [x] 2.1 Implementar o registro de jobs ativos por grupo e a política `parallel`, com teste de que dois jobs independentes coexistem
- [x] 2.2 Implementar a política `latest_wins` (cancela e descarta mensagens do job anterior), com teste de substituição que confirma token limpo no job novo
- [x] 2.3 Implementar a política `serialize` com fila FIFO por grupo e descarte por `key`, com teste de que requisição duplicada é descartada e a execução não é paralela
- [x] 2.4 Implementar `cancel(job_id)`/`cancel_group`/`cancel_all` sem afetar jobs não relacionados, com teste de cancelamento isolado por job

## 3. Pump e watchdog

- [x] 3.1 Implementar o pump único que drena as filas de todos os jobs na thread do Tk e despacha eventos aos callbacks; verificar com teste que o callback é chamado na thread do Tk
- [x] 3.2 Implementar o watchdog centralizado de liveness e inatividade (120s) publicando o término, com teste de job morto sem término e de job sem progresso
- [x] 3.3 Garantir que o cancelamento drena e finaliza a UI sem aguardar o worker, com teste que cancela e confirma o término imediato mesmo com a thread viva
- [x] 3.4 Iniciar/parar o pump conforme houver jobs ativos, com teste de que o `after` não fica órfão após o último job

## 4. Integração com o estado ocupado

- [x] 4.1 Emitir eventos `job_iniciado`/`job_terminado` e registrar no wiring os callbacks que acionam `presenter.enter/exit` e `job_cancelavel_iniciado/finalizado`; verificar com teste de ciclo de vida equilibrado
- [x] 4.2 Cobrir substituição, cancelamento e falha com teste de que a contagem de operações ativas retorna ao valor anterior e o cursor não fica preso

## 5. Porte dos jobs existentes

- [x] 5.1 Portar `FundamentalJob` para o manager preservando geração, progresso e watchdog, e verificar `test_fundamental_job.py` e `test_cancelamento_integracao.py`
- [x] 5.2 Portar `DocumentosJob` e verificar o fluxo de aquisição e o watchdog
- [x] 5.3 Portar `NoticiasJob` e verificar o fluxo de aquisição, cancelamento e remontagem
- [x] 5.4 Portar `ResumosPendentesJob` preservando a gravação no worker e a reflexão na thread do Tk, e verificar `test_resumos_job.py`
- [x] 5.5 Portar as threads inline (preview/resumo avulso, chat, teste de config LLM, verificação de versão) para o manager e verificar os testes correspondentes. Preview/resumo avulso, teste de config LLM e verificação de versão foram portados nesta change; o **envio do chat** foi transferido para a change `cache-prompt-chat` (seção 5), que já depende desta e deve ser aplicada futuramente para concluir o porte.
- [x] 5.6 Remover das classes de job a thread, a fila e o watchdog próprios, deixando apenas a função de trabalho e a configuração de política, e verificar que não resta `threading.Thread`/`fila.put(True)` nesses módulos
- [x] 5.7 Reduzir os testes de coreografia dos jobs ao trabalho puro (headless), eliminando a duplicação coberta pelo manager, e verificar que `test_fundamental_job.py` e `test_resumos_job.py` continuam sem `@needs_display`

## 6. Orçamento de testes de UI

<!-- Esta seção entrega a primeira fatia do orçamento (baseline 250 + guardrail
     que só reprova aumento + migração do TestPreview + conversão headless dos
     jobs). O `reduzir-testes-ui` completa o desenho: move o baseline para
     `ui_test_budget.txt`, adiciona o ratchet (queda exige atualização) e segue
     baixando o teto a partir de 250. -->

- [x] 6.1 Registrar a contagem baseline de testes decorados com `@needs_display` e adicionar guardrail (teste arquitetural) que reprova o aumento dessa contagem
- [x] 6.2 Migrar testes de lógica pura hoje em `tests/test_presentation` (ex.: `TestPreview` de `flowscope.application.document_preview`) para `tests/test_application`/`tests/test_domain`, e verificar que rodam sem `DISPLAY`
- [x] 6.3 Substituir por headless os testes de UI que só exercitavam processamento (preview em thread, cache de texto, lote no painel) e confirmar que a contagem de `@needs_display` não aumentou

## 7. Verificação final

- [x] 7.1 Rodar a suíte de apresentação completa e confirmar paridade de mensagens, estados de botão e ordem de exibição
- [x] 7.2 Rodar `ruff` e a checagem de fronteiras de camadas e confirmar ausência de novas violações
