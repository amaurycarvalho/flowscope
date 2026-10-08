## 1. Contrato de desfecho (aditivo)

- [ ] 1.1 Adicionar `Outcome` (`SUCESSO`/`FALHA`/`CANCELADO`/`ABORTADO`), o campo `Erro.fatal: bool = False` e `Termino(outcome, falha_reportada)`, mantendo `cancelado` como propriedade derivada (`outcome is CANCELADO`); verificar com teste unitário em `tests/test_presentation/` cobrindo a construção e o default retrocompatível.
- [ ] 1.2 Adicionar `JobContext.falhar(exc, dados=None)` que publica `Erro(fatal=True)` e marca o desfecho `FALHA`, mantendo `ctx.erro` como falha de item (`fatal=False`, sem alterar desfecho); verificar com teste que `ctx.erro` não muda o desfecho e `ctx.falhar` muda.
- [ ] 1.3 Em `BackgroundManager._trabalhar`, derivar o desfecho por escape (retorno → `SUCESSO`, `OperacaoCancelada` → `CANCELADO`, `Exception` → `ctx.falhar`) e, no `finally`, marcar `FALHA` quando o desfecho continuar indefinido (cobre `BaseException` e `trabalho=None`); verificar com testes de manager para cada caminho.
- [ ] 1.4 Fazer `_finalizar` receber o desfecho e o watchdog (`_aplicar_watchdog`) encerrar com `ABORTADO` nos dois ramos (thread morta/fila vazia e inatividade); verificar com testes que o `Termino` publicado carrega `ABORTADO`.
- [ ] 1.5 Fazer `_invocar` retornar `bool` (sucesso do callback) e registrar `handle.falha_reportada` ao despachar falha fatal; verificar com teste que callback ausente/que falha deixa `falha_reportada=False` e callback bem-sucedido deixa `True`.

## 2. Ligação ao presenter e política de status

- [ ] 2.1 Repassar `handle.outcome` e `handle.falha_reportada` ao presenter em `_on_background_terminado` (`app_wiring.py`); verificar com teste de wiring que o término entrega esses valores.
- [ ] 2.2 No presenter, ao zerar a contagem, decidir o aviso pelo desfecho agregado com precedência `falha_nao_reportada > cancelado > abortado`, sem escrever em `SUCESSO`/`FALHA` já reportada; verificar com testes em `test_presenter.py` para cada precedência.
- [ ] 2.3 Fazer `request_cancel()` delegar apenas a `background.cancel_all()` e remover a leitura de `_cancel_token` em `exit()`, removendo o token global; verificar atualizando `test_presenter.py` e `test_cancelamento_integracao.py` para assertar o desfecho.
- [ ] 2.4 Instalar `threading.excepthook` para registrar no logger do app as exceções que escapam de workers; verificar com teste que um worker que lança `BaseException` produz entrada de log e UI avisada pelo fallback.

## 3. Migração dos sítios de falha fatal

- [ ] 3.1 Migrar `controller_data.py` (`ctx.erro` → `ctx.falhar` nos caminhos fatais) e verificar com os testes de carga principal.
- [ ] 3.2 Migrar `fundamental_job.py` (`ctx.erro` → `ctx.falhar`) e verificar com os testes de job fundamentalista.
- [ ] 3.3 Migrar `chat/envio.py` (`ctx.erro` fatal → `ctx.falhar`, preservando o `dados` de indisponível/erro) e verificar com os testes de envio do chat.

## 4. Mensagens honestas e fallback de pré-visualização

- [ ] 4.1 Fazer `AquisicaoDocumentos.adquirir` e `AquisicaoNoticias.adquirir` retornarem a contagem de itens persistidos e usar a contagem nas mensagens de conclusão (sucesso vs. neutra), sem afirmar atualização quando nada foi adquirido; verificar com testes de painel de documentos e notícias conforme as specs.
- [ ] 4.2 Adicionar `ao_erro` ao submit da pré-visualização em `document_flow_mixin.py`, saindo do estado de carregamento com mensagem informativa e guardando a seleção corrente; verificar com testes de painel de documentos e notícias.

## 5. Validação final

- [ ] 5.1 Rodar `openspec validate desfecho-termino-status --strict`, o lint, o complexity e a suíte de testes; verificar zero erros e confirmar que nenhum caminho de término deixa a barra de status sem informar interrupção, aborto ou falha.
