## 1. ProgressReporter — classe de progresso

- [x] 1.1 Criar `src/flowscope/presentation/gui/progress.py` com a classe `ProgressReporter` e `ProgressStep` (dataclass), incluindo `start_phase()`, `advance()`, `fail()`, `finish_phase()` e sistema de pesos relativos
- [x] 1.2 Adicionar throttling no callback `_on_update`: só atualizar GUI se progresso variou >1% ou >100ms desde última atualização
- [x] 1.3 Criar testes unitários para `ProgressReporter` no diretório `tests/` cobrindo: avanço normal, falhas, múltiplas fases com pesos, fase com total=0

## 2. Statusbar widget — barra de progresso + label

- [x] 2.1 Modificar `_build_statusbar()` em `app.py`: substituir `tk.Label` por `tk.Frame` contendo `tk.Label` (texto) + `ttk.Progressbar` (modo 'determinate')
- [x] 2.2 Adicionar método `_set_progress(current: int, total: int, label: str)` que atualiza label e barra
- [x] 2.3 Remover `_animate_loading()` e substituir por chamadas ao `ProgressReporter`
- [x] 2.4 Manter `_flash_status()` para mensagens pós-carregamento (ex: "✓ 87 tickers carregados")

## 3. Conectar ProgressReporter ao pipeline de dados

- [x] 3.1 Modificar `AnalyzeTickersUseCase.execute()` para aceitar `progress_callback: Callable | None = None` e repassar ao repository e engine
- [x] 3.2 Modificar `B3DataRepository.fetch_trades()` para aceitar `progress_callback` e invocar a cada data processada (sucesso ou falha)
- [x] 3.3 Modificar `B3Client.fetch_file()` para aceitar `progress_callback` e invocar no cache-hit e após download+parse
- [x] 3.4 Modificar `IndicatorEngine.execute()` para aceitar `progress_callback` e invocar a cada indicador processado (ou a cada lote de tickers)
- [x] 3.5 Modificar `B3Client.fetch_portfolio()` para aceitar `progress_callback` e invocar durante portfolio loading

## 4. Integrar na GUI

- [x] 4.1 Em `_on_load_data()`, instanciar `ProgressReporter` com callback `_set_progress` e passá-lo ao `UseCase.execute()`
- [x] 4.2 Em `_fill_with_index()`, criar `ProgressReporter` e passar ao `fetch_portfolio()`, com fases: portfolio → (se houver) carregamento de dados
- [x] 4.3 Em `_ensure_tickers()`, garantir que o portfolio loading automático dispare o progresso
- [x] 4.4 Garantir que `_exit_loading_state()` é chamado no `finally` e transiciona para estado "Pronto." com flash de 2.5s

## 5. Tratamento de falhas e cache

- [x] 5.1 No `ProgressReporter`, implementar `fail(n, detail)` que incrementa contador de falhas e inclui no label (ex: "3/7 (1 falhou)")
- [x] 5.2 Em `fetch_trades()`, invocar `progress_callback` mesmo quando uma data lança exceção (usando `fail=True`)
- [x] 5.3 Em `fetch_file()`, se dados em cache, invocar callback imediatamente com avanço sem delay
- [x] 5.4 Garantir que falhas em todas as datas não impedem a conclusão do progresso (barra chega a 100%)

## 6. Verificação

- [x] 6.1 Executar `flowscope` (sem args) — confirmar que GUI abre e statusbar funciona *(manual)*
- [x] 6.2 Clicar "Carregar" com dados não cacheados — confirmar progresso por data *(manual)*
- [x] 6.3 Clicar "Carregar" com todos os dados em cache — confirmar barra preenche rápido e mostra "Pronto." *(manual)*
- [x] 6.4 Clicar IBOV/IDIV/IFIX — confirmar "Baixando portfólio..." aparece *(manual)*
- [x] 6.5 Testar com data inválida (ex: feriado) — confirmar falha é contabilizada no progresso *(manual)*
- [x] 6.6 Verificar que `--gui` explícito e `--version` continuam funcionando (nada foi quebrado)
