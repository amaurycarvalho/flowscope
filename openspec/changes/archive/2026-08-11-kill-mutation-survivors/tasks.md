## 1. Módulo: clipboard_image (62 survivors)

- [x] 1.1 Ler `src/flowscope/infrastructure/clipboard_image.py` e `tests/test_infrastructure/test_clipboard_image.py`
- [x] 1.2 Analisar cada survivor no log (mutmut_7 a mutmut_36) e mapear para função/branch
- [x] 1.3 Fortalecer `test_linux_calls_xclip`: adicionar asserts sobre `check=True`, argumentos `xclip`, `-selection`, `clipboard`, `-t`, `image/png`
- [x] 1.4 Fortalecer `test_macos_calls_osascript`: adicionar asserts sobre `capture_output=True`, `text=True`, `check=False`, argumentos `osascript`, `-e`
- [x] 1.5 Adicionar teste para `copy_image_to_clipboard` que verifica argumentos de `figure.savefig` (format, dpi, bbox_inches)
- [x] 1.6 Fortalecer `test_windows_fallback_powershell_on_import_error`: asserts sobre `check=True` e argumentos do powershell
- [x] 1.7 Rodar `pytest tests/test_infrastructure/test_clipboard_image.py -v` e corrigir falhas

## 2. Módulo: cache (38 survivors)

- [x] 2.1 Ler `src/flowscope/infrastructure/cache.py` e `tests/test_infrastructure/test_cache.py`
- [x] 2.2 Analisar survivors (mutmut_1 a mutmut_46) no log do mutmut
- [x] 2.3 Adicionar testes para `CacheManager._path_for`: verificar formato do path com strftime
- [x] 2.4 Adicionar testes para `CacheManager.find_nearest`: data exata, data próxima, max_deviation, sem cache
- [x] 2.5 Fortalecer `test_put_and_get`: verificar conteúdo gravado com `encoding="utf-8"` exato
- [x] 2.6 Fortalecer `test_cache_valido_retorna_dado_sem_executar_fetch`: verificar `encoding` e `indent` na escrita
- [x] 2.7 Fortalecer `test_cache_ausente_executa_fetch`: verificar argumentos de `write_text` e `mkdir`
- [x] 2.8 Rodar `pytest tests/test_infrastructure/test_cache.py -v` e corrigir falhas

## 3. Módulo: generators (31 survivors)

- [x] 3.1 Ler `src/flowscope/infrastructure/b3/generators.py` e `tests/test_infrastructure/test_sampling_calendar.py`
- [x] 3.2 Analisar survivors no log (mutmut_1 a mutmut_40)
- [x] 3.3 Adicionar testes parametrizados para `_fibs_up_to` com diferentes limites
- [x] 3.4 Adicionar testes para `_fibonacci_double_dates` com `period_days <= 30` e `> 30`
- [x] 3.5 Adicionar testes para `_monte_carlo_dates` verificando offsets gerados
- [x] 3.6 Rodar `pytest tests/test_infrastructure/test_sampling_calendar.py -v` e corrigir falhas

## 4. Módulo: b3/calendar (20 survivors)

- [x] 4.1 Ler `src/flowscope/infrastructure/b3/calendar.py` e `tests/test_infrastructure/test_b3_calendar.py`
- [x] 4.2 Analisar survivors no log
- [x] 4.3 Adicionar testes para `_find_nearest_with_data` com `has_data=Callable` e `has_data=None`
- [x] 4.4 Adicionar testes para `_resolve_with_data` com lista vazia, datas sem dados, duplicadas
- [x] 4.5 Adicionar testes para `resolve_dates` com e sem `has_data`
- [x] 4.6 Adicionar testes para `fibonacci_dates` com e sem `has_data`
- [x] 4.7 Rodar `pytest tests/test_infrastructure/test_b3_calendar.py -v` e corrigir falhas

## 5. Módulo: b3/repository (49 survivors)

- [x] 5.1 Ler `src/flowscope/infrastructure/b3/repository.py` e `tests/test_infrastructure/test_b3_repository.py`
- [x] 5.2 Analisar survivors no log
- [x] 5.3 Adicionar teste para `_has_data`: conteúdo vazio, header sem dados, dados válidos
- [x] 5.4 Adicionar teste para `get_available_dates` com métodos válidos e inválidos
- [x] 5.5 Adicionar teste para `fetch_trades` com `cache_only=True` e `cache_only=False`
- [x] 5.6 Adicionar teste para `fetch_trades` verificando chamada a `progress_callback`
- [x] 5.7 Fortalecer asserts sobre argumentos de `fetch_file` (date, progress_callback, cache_only)
- [x] 5.8 Rodar `pytest tests/test_infrastructure/test_b3_repository.py -v` e corrigir falhas

## 6. Módulos: domain/strategies (135+ survivors)

- [x] 6.1 Mapear survivors de volume (34), flow (26), dominance (20), conviction (20), indicators (20), density (12), money_flow (11), demais
- [x] 6.2 Para `volume`: revisar asserts nos testes existentes (`test_indicators.py`, `test_dominance_strategies.py`)
- [x] 6.3 Para `flow`: adicionar testes para edge cases (zero, None, valores negativos)
- [x] 6.4 Para `dominance` classifiers: adicionar testes parametrizados com valores boundary
- [x] 6.5 Para `conviction` classifiers: adicionar testes parametrizados com valores boundary
- [x] 6.6 Para `indicators`: revisar e fortalecer asserts de cálculos matemáticos
- [x] 6.7 Rodar `pytest tests/test_domain/ -v` e corrigir falhas

## 7. Módulo: b3/parser (112 survivors)

- [x] 7.1 Ler `src/flowscope/infrastructure/b3/parser.py` e `tests/test_infrastructure/test_b3_parser.py`
- [x] 7.2 Analisar survivors no log - identificar campos de CSV não validados
- [x] 7.3 Adicionar asserts sobre campos específicos do CSV parseado (preço, volume, ticker, tipo de negociação)
- [x] 7.4 Adicionar testes para edge cases: CSV vazio, header sem dados, campos inválidos
- [x] 7.5 Rodar `pytest tests/test_infrastructure/test_b3_parser.py -v` e corrigir falhas

## 8. Módulo: b3/client (99 survivors)

- [x] 8.1 Ler `src/flowscope/infrastructure/b3/client.py` e `tests/test_infrastructure/test_b3_client.py`
- [x] 8.2 Analisar survivors - focar em `_request_token`, `_download_csv`, `_bust_stale_portfolio_cache`
- [x] 8.3 Fortalecer asserts sobre `requests.get`: verificar `params`, `timeout`, `url`
- [x] 8.4 Adicionar teste para `_bust_stale_portfolio_cache`: arquivo existe, arquivo não existe, JSON inválido
- [x] 8.5 Rodar `pytest tests/test_infrastructure/test_b3_client.py -v` e corrigir falhas

## 9. Módulo: application/use_cases (144 survivors)

- [x] 9.1 Ler `src/flowscope/application/use_cases.py` e `tests/test_application/test_use_cases.py`
- [x] 9.2 Analisar survivors no log - identificar use cases com baixa cobertura de branches
- [x] 9.3 Adicionar testes para cenários de erro e edge cases nos use cases
- [x] 9.4 Fortalecer asserts sobre chamadas a repositórios e serviços
- [x] 9.5 Rodar `pytest tests/test_application/ -v` e corrigir falhas

## 10. Módulo: presentation/cli (68 survivors)

- [x] 10.1 Ler `src/flowscope/presentation/cli.py` e `tests/test_presentation/`
- [x] 10.2 Analisar survivors e adicionar testes onde aplicável (CLI é difícil de testar unitariamente)
- [x] 10.3 Rodar `pytest tests/test_presentation/ -v` e corrigir falhas

## 11. Módulo: presentation/shortcuts (54 survivors)

- [x] 11.1 Ler `src/flowscope/presentation/shortcuts.py` e testes correspondentes
- [x] 11.2 Analisar survivors e adicionar/fortalecer testes
- [x] 11.3 Rodar `pytest tests/test_presentation/ -v` e corrigir falhas

## 12. Módulos restantes (presentation/main, logging, domain/engine, domain/value_objects)

- [x] 12.1 Analisar e tratar survivors em `presentation/main` (17), `logging` (16), `engine` (9), `value_objects` (7), demais
- [x] 12.2 Rodar pytest nos arquivos de teste correspondentes

## 13. Configuração: do_not_mutate_patterns

- [x] 13.1 Identificar padrões de mutantes impossíveis de matar com teste unitário
- [x] 13.2 Adicionar entradas ao `do_not_mutate_patterns` no `pyproject.toml`
- [x] 13.3 Verificar que `pyproject.toml` continua válido sintaticamente

## 14. Validação final

- [x] 14.1 Rodar `make lint` e corrigir quaisquer erros de lint
- [x] 14.2 Rodar `make test` (suíte completa) e corrigir quaisquer falhas
- [x] 14.3 Confirmar que todos os arquivos de teste novos/modificados estão limpos e passando
