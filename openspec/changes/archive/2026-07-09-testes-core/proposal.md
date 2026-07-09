## Why

Cobertura de testes atual é de ~35% (160 testes, 3329 statements). As camadas de domínio (94%) estão sólidas, mas application (56%) e infrastructure (42%) têm lacunas significativas que aumentam risco de regressão em lógica crítica de orquestração, I/O e cache. Esta mudança fecha essas lacunas com testes baseados em mocking, tornando o core não-GUI robusto antes de avançar em novas funcionalidades.

## What Changes

- Testar `AnalyzeTickersUseCase.execute()` com trades mockados, incluindo fluxo com/sem filtro de tickers e agregação de dados diários
- Testar `OperationGuard.acquire()` nos dois estados (livre e ocupado), incluindo reentrância
- Testar `LoadIndexPortfolioUseCase.execute()` com índices válidos e inválidos, retorno vazio e sucesso
- Testar `CacheManager.get_or_fetch()` com cache válido, expirado, ausente, e falha no fetch
- Testar `CacheManager.invalidate()` com chave existente e inexistente
- Testar `B3Client.fetch_file()` com cache hit, cache miss (HTTP mockado), e callback de progresso
- Testar `B3Client.fetch_portfolio()` com retorno de tickers, resposta vazia, e falha HTTP
- Testar `B3DataRepository.fetch_trades()` com parser sucesso, erro de parse, e erro de download
- Testar `B3Client._build_portfolio_url()` para verificação do encoding base64
- Adicionar `responses` (ou `pytest-httpserver`) como dependência de desenvolvimento para mock HTTP
- Adicionar `pytest-mock` ou usar `unittest.mock` padronizado via conftest

## Capabilities

### New Capabilities
- `test-infra-mocking`: Infraestrutura de testes com mock HTTP (`responses`/`pytest-httpserver`) e fixtures padronizadas para B3Client, CacheManager e DataRepository

### Modified Capabilities
<!-- Nenhuma — esta mudança não altera requisitos de comportamento de specs existentes, apenas adiciona testes -->

## Impact

- `pyproject.toml`: adicionar `responses` em `[project.optional-dependencies] dev`
- `tests/conftest.py`: novas fixtures para `B3Client` mockado, `CacheManager` com temp_dir, `B3DataRepository`
- `tests/test_infrastructure/`: novos arquivos `test_b3_client.py`, expansão de `test_b3_repository.py` e `test_cache.py`
- `tests/test_application/`: novos testes em `test_use_cases.py`, novo arquivo `test_load_portfolio.py`, `test_operation_guard.py`
- Nenhuma modificação em código de produção — mudança exclusiva de testes
