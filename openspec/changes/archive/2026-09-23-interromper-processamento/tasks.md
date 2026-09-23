## 1. Núcleo de cancelamento (application)

- [x] 1.1 Criar `src/flowscope/application/cancellation.py` com a exceção `OperacaoCancelada` e o token de cancelamento baseado em `threading.Event` (expondo checagem/sinalização/limpeza). Verificar com teste unitário em `tests/test_application/` que cobre sinalizar, observar e limpar
- [x] 1.2 Adicionar parâmetro opcional de token a `FundamentalAnalysisUseCase.execute` e checar no topo do laço por ticker, fora do `try/except` tolerante, lançando `OperacaoCancelada`; verificar teste que garante que o laço para na unidade seguinte e que `houve_falha_recuperavel` não é marcado
- [x] 1.3 Adicionar parâmetro opcional de token a `AquisicaoDocumentos.adquirir` e checar nos laços de `_adquirir_fii` e `_adquirir_acao`; verificar teste em `tests/test_infrastructure/` de que documentos restantes não são adquiridos após o cancelamento
- [x] 1.4 Fazer `ResumosPendentesJob` observar o token nos laços de `_preparar_textos` e `_resumir`, lançando `OperacaoCancelada`; verificar teste em `tests/test_presentation/test_resumos_job.py` de que o lote para sem processar as unidades seguintes

## 2. Presenter como autoridade do cancelamento

- [x] 2.1 Adicionar ao `FlowScopePresenter` o token, o contador `_jobs_cancelaveis`, `request_cancel()`, `job_cancelavel_iniciado()`, `job_cancelavel_finalizado()` e acesso ao token para os jobs; limpar o token apenas na transição 0→1 em `enter()`; verificar testes em `tests/test_presentation/test_presenter.py`
- [x] 2.2 Em `exit()`, na transição para ocioso, detectar token setado, delegar `set_cancellable(False)` e publicar a mensagem "Processamento interrompido." na barra de status; verificar teste de que a mensagem é emitida uma única vez e que operação normal não a emite
- [x] 2.3 Garantir que iniciar job sobreposto com token setado não limpa a solicitação (contador > 0 não redefine o token); verificar teste de operações sobrepostas

## 3. Botão e barra de status (GUI)

- [x] 3.1 Criar o botão de interromper em `_build_statusbar` com o ícone `process-stop.png`, empacotado à esquerda da barra de progresso e inicialmente oculto, com comando ligado a `request_cancel()` do presenter e referência de imagem preservada; verificar teste de que o botão existe e está oculto ao iniciar
- [x] 3.2 Implementar `set_cancellable(bool)` na view para mostrar/ocultar o botão conforme o contador de jobs canceláveis, sem alterar a visibilidade da barra; verificar teste de mostrar/ocultar
- [x] 3.3 Garantir que `_set_status`, `_flash_status` e `clear_progress` ocultam o botão junto com a barra; verificar teste de que a carga síncrona (que usa `_set_progress`) não exibe o botão

## 4. Tratamento de cancelamento nos jobs

- [x] 4.1 Fazer `FundamentalJob` receber o token, repassá-lo ao caso de uso e capturar `OperacaoCancelada` antes do `except Exception`, sem publicar `MENSAGEM_ERRO` nem logar falha; verificar teste em `tests/test_presentation/test_fundamental_job.py`
- [x] 4.2 Fazer `DocumentosJob` receber o token, repassá-lo à aquisição e capturar `OperacaoCancelada` antes do `except Exception`, sem warning, publicando o término; verificar teste de que a fila termina e nenhum aviso de falha é registrado
- [x] 4.3 Fazer `ResumosPendentesJob` capturar `OperacaoCancelada` no `_executar` sem vazar exceção para o excepthook da thread, publicando o término; verificar teste de que a thread encerra limpa

## 5. Orquestração dos fluxos em background

- [x] 5.1 Em `controller_fundamental.py`, iniciar o job como cancelável, obter o token do presenter, detectar o cancelamento na drenagem e finalizar imediatamente (sem aguardar a thread) descartando resultado parcial; verificar teste de que o resultado não é aplicado e a UI volta ao estado ocioso
- [x] 5.2 Em `app_actions.py`, iniciar a aquisição como cancelável, finalizar imediatamente ao detectar o token e suprimir o flash "Documentos atualizados!" quando interrompida; verificar teste em `tests/test_presentation/` de supressão
- [x] 5.3 Em `app_resumos_actions.py`, iniciar o lote como cancelável, marcar `_resumos_interrompido` no cancelamento e suprimir o flash "Resumos gerados"; verificar teste de supressão e de finalização

## 6. Integração e qualidade

- [x] 6.1 Escrever teste de integração que aciona o botão durante um job fake em background e verifica, de ponta a ponta, que o laço para, barra e botão somem, controles/cursor são restaurados e a statusbar exibe "Processamento interrompido."
- [x] 6.2 Rodar `make lint` e `make test` e confirmar que passam (incluindo a cobertura mínima de 85%)
