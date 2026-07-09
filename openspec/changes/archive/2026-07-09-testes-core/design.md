## Context

Test coverage atual: 35% geral. Domain layer em 94% (bem testado), mas application (56%) e infrastructure (42%) têm lacunas. A camada de presentation/GUI tem 19% e fica fora do escopo desta mudança — é intrinsecamente difícil de testar (Tkinter + matplotlib).

Projeto usa `pytest`, `unittest.mock`, e fixtures em `tests/conftest.py`. Já existe padrão de `MagicMock` para repositórios. Não há uso atual de mock HTTP — os testes de `B3Client` simplesmente não existem.

## Goals / Non-Goals

**Goals:**
- Elevar cobertura de application/ de 56% para >90%
- Elevar cobertura de infrastructure/ de 42% para >75%
- Estabelecer padrão de mock HTTP com `responses` para `B3Client`
- Criar fixtures reutilizáveis para `B3Client` mockado, `CacheManager` com `tmp_path`, e `B3DataRepository`
- Testar todos os fluxos de erro (HTTP failures, cache expirado, parser errors, portfolios vazios)

**Non-Goals:**
- Não testar presentation/GUI (app.py, charts, widgets, controller, presenter)
- Não alterar código de produção — mudança exclusiva de testes
- Não adicionar testes de integração ponta-a-ponta com B3 real
- Não adicionar testes de performance ou stress

## Decisions

| Decisão | Opção Escolhida | Alternativa Considerada | Motivo |
|---------|----------------|------------------------|--------|
| Mock HTTP | `responses` | `pytest-httpserver`, `unittest.mock` direto | `responses` é mais idiomático para mock de `requests.get`, intercepta em nível de transporte, e não requer servidor real |
| Mock de arquivos | `tmp_path` (pytest built-in) | `tempfile`, `monkeypatch` | `tmp_path` é a fixture padrão do pytest, já usada em `test_cache.py`, consistente |
| Organização dos testes | 1 arquivo por módulo | 1 arquivo gigante | Padrão já existente no projeto (ex: `test_b3_parser.py`, `test_cache.py`). Clareza e manutenibilidade |
| Fixtures de TradeDay | Reutilizar `mock_trades` do `conftest.py` | Criar fixtures locais | Evita duplicação, consistente com padrão existente |
| Dependência | `responses` em `[dev]` | `VCR.py` (grava/replay) | `responses` é mais leve, não requer cassetes, e o foco é testar lógica, não gravar tráfego real |

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Mock HTTP pode divergir do comportamento real da B3 | Testes mockam apenas cenários conhecidos (cache hit/miss, erro HTTP). Testes de integração com B3 real são deixados para outro change |
| `responses` adiciona dependência de desenvolvimento | Dependência leve, sem impacto em produção. Instalada apenas via `pip install -e ".[dev]"` |
| Tests de `AnalyzeTickersUseCase` dependem do engine real | O engine já é bem testado (94%). Usar o `IndicatorEngine` real valida a integração sem duplicar mocks |
