## 1. Setup de Dependências e Fixtures

- [x] 1.1 Adicionar `responses` em `pyproject.toml` na seção `[project.optional-dependencies] dev`
- [x] 1.2 Rodar `pip install -e ".[dev]"` para instalar nova dependência
- [x] 1.3 Criar fixture `responses` no `conftest.py` ou usar import direto nos testes
- [x] 1.4 Criar fixture `mock_b3_client` completa em `conftest.py` com suporte a respostas HTTP mockadas
- [x] 1.5 Criar fixture `mock_b3_data_repository` em `conftest.py` com `B3DataRepository` usando `mock_b3_client`

## 2. CacheManager — get_or_fetch e invalidate

- [x] 2.1 Implementar `test_get_or_fetch_cache_valido` — cache dentro do TTL retorna dado sem executar fetch_fn
- [x] 2.2 Implementar `test_get_or_fetch_cache_expirado` — cache fora do TTL executa fetch_fn e atualiza
- [x] 2.3 Implementar `test_get_or_fetch_cache_ausente` — sem cache existente, executa fetch_fn e armazena
- [x] 2.4 Implementar `test_invalidate_chave_existente` — arquivo de cache é removido do disco
- [x] 2.5 Implementar `test_invalidate_chave_inexistente` — não levanta exceção

## 3. B3Client — fetch_file com cache hit/miss e falha HTTP

- [x] 3.1 Implementar `test_fetch_file_cache_hit` — dado em cache retorna sem requisição HTTP
- [x] 3.2 Implementar `test_fetch_file_cache_miss` — sem cache, faz requisição HTTP, armazena e retorna
- [x] 3.3 Implementar `test_fetch_file_erro_http` — HTTP 500 levanta RuntimeError
- [x] 3.4 Implementar `test_fetch_file_com_callback_cache_hit` — callback invocado com mensagem de cache
- [x] 3.5 Implementar `test_fetch_file_com_callback_cache_miss` — callback invocado durante download

## 4. B3Client — fetch_portfolio com respostas válida, vazia e falha

- [x] 4.1 Implementar `test_fetch_portfolio_sucesso` — retorna lista de tickers do CSV decodificado
- [x] 4.2 Implementar `test_fetch_portfolio_resposta_vazia` — resposta vazia retorna lista vazia
- [x] 4.3 Implementar `test_fetch_portfolio_erro_http` — falha HTTP retorna lista vazia
- [x] 4.4 Implementar `test_build_portfolio_url` — verifica encoding base64 do payload JSON

## 5. B3DataRepository — fetch_trades com parser e download

- [x] 5.1 Implementar `test_fetch_trades_multiplas_datas` — processa 2 datas com CSV válido
- [x] 5.2 Implementar `test_fetch_trades_ignora_parse_error` — data com CSV inválido é ignorada, data válida é processada
- [x] 5.3 Implementar `test_fetch_trades_ignora_download_error` — data com falha HTTP é ignorada
- [x] 5.4 Implementar `test_fetch_trades_filtro_tickers` — apenas trades dos tickers especificados são retornados

## 6. Use Cases — AnalyzeTickersUseCase

- [x] 6.1 Implementar `test_execute_com_tickers` — resultado contém dados por ticker (vwap, volume_profile, etc.)
- [x] 6.2 Implementar `test_execute_sem_tickers` — usa top_tickers do engine para definir quais incluir
- [x] 6.3 Implementar `test_execute_com_progress_callback` — callback é invocado durante execução
- [x] 6.4 Implementar `test_execute_sem_trades` — repositório vazio retorna dict vazio

## 7. OperationGuard — acquire livre e ocupado

- [x] 7.1 Implementar `test_acquire_quando_livre` — context manager retorna True
- [x] 7.2 Implementar `test_acquire_quando_ocupado` — segunda chamada retorna False
- [x] 7.3 Implementar `test_acquire_volta_a_True_apos_liberacao` — após sair do with, novo acquire retorna True

## 8. LoadIndexPortfolioUseCase — validação e erros

- [x] 8.1 Implementar `test_execute_indice_valido` — IBOV/IDIV/IFIX retorna lista de tickers
- [x] 8.2 Implementar `test_execute_indice_invalido` — índice inválido levanta InvalidIndexError
- [x] 8.3 Implementar `test_execute_portfolio_vazio` — repositório vazio levanta PortfolioNotFoundError

## 9. Verificação Final

- [x] 9.1 Rodar `python -m pytest tests/ -v --tb=short` — todos os 160+ testes existentes + novos passam
- [x] 9.2 Rodar `python -m pytest tests/ --cov=src/flowscope --cov-report=term-missing` — verificar coverage final
- [x] 9.3 Confirmar que cobertura de `application/` subiu para >90% e de `infrastructure/` para >75%
