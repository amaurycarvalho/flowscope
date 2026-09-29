## 1. Cancelamento nas camadas de aplicação e infraestrutura

- [ ] 1.1 Adicionar `cancel_token` opcional a `LoadIndexPortfolioUseCase.execute` e verificar com teste de application que a interrupção é observada
- [ ] 1.2 Adicionar `cancel_token` opcional a `AnalyzeTickersUseCase.execute` e verificar entre fases e no laço de tickers
- [ ] 1.3 Repassar o token a `DataRepository.get_index_tickers`/`fetch_trades` e implementar a checagem em `B3DataRepository`, com teste de infraestrutura da interrupção
- [ ] 1.4 Adicionar callback de cancelamento opcional (`Callable[[], bool]`) ao `IndicatorEngine` e adaptá-lo no caso de uso, mantendo `domain` sem importar `application`; verificar o teste de fronteiras
- [ ] 1.5 Garantir que o worker descarta o resultado parcial ao detectar cancelamento, com teste de que nenhum resultado interrompido é aplicado

## 2. Submissão da carga principal ao manager

- [ ] 2.1 Converter `on_load_data` em submissão ao grupo `"carga"` (`latest_wins`, `key` derivada de ref_date/período/amostragem) e verificar com teste headless (presenter fake) que a thread do Tk não é bloqueada e o job é submetido
- [ ] 2.2 Converter `on_index_clicked` (IBOV/IDIV/IFIX) para o mesmo grupo e verificar que dois índices distintos se substituem
- [ ] 2.3 Converter a carga de portfólio de `on_ticker_edit` para o grupo `"carga"` e verificar que não resta chamada de rede síncrona
- [ ] 2.4 Mover a criação e o avanço do `ProgressReporter` para o worker, publicando `(current, total, label)` por evento, e verificar a barra de progresso com o teste de progress
- [ ] 2.5 Entregar o resultado por evento e executar `on_portfolio_loaded`/`on_result`/`_iniciar_analise_fundamental` na thread do Tk, verificando o encadeamento fundamentalista

## 3. Concorrência: reentrada versus nova operação

- [ ] 3.1 Estreitar o `OperationGuard` ao setup síncrono do controller e verificar que ele não bloqueia o supersede
- [ ] 3.2 Implementar o descarte por `key` para requisição idêntica ativa e verificar com teste que o clique repetido não reinicia a carga
- [ ] 3.3 Verificar com teste que uma nova carga distinta cancela a anterior e o job novo inicia com token limpo

## 4. Estado ocupado e cancelamento visível

- [ ] 4.1 Exibir o botão de interromper durante a carga principal via eventos de ciclo de vida e verificar com teste headless de integração de cancelamento (presenter fake), mantendo em UI apenas o wiring do botão
- [ ] 4.2 Interromper a carga principal pelo botão e verificar, sem Tk, que controles/cursor são restaurados e o resultado é descartado, com a statusbar exibindo "Processamento interrompido."
- [ ] 4.3 Verificar que a substituição não restaura controles nem cursor entre as cargas

## 5. Orçamento de testes de UI

- [ ] 5.1 Testar submissão, `key`/supersede, tokens e descarte por evento com presenter fake, sem `@needs_display`
- [ ] 5.2 Confirmar que a contagem de `@needs_display` não aumentou em relação ao baseline registrado na fatia A, e que os únicos testes UI cobre o wiring do botão de interromper

## 6. Verificação final

- [ ] 6.1 Atualizar os deltas de `process-cancellation`, `loading-state-management` e `presentation-test-coverage` e validar o change
- [ ] 6.2 Rodar a suíte de apresentação, os testes de cancelamento/integração, testes de complexidade e a checagem de fronteiras, confirmando paridade de rótulos, mensagens e ordem de exibição
