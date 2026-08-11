## Why

O mutation score atual do flowscope está em 61.95% (1,446 killed de 2,493 mutantes, 886 sobreviventes), abaixo do patamar mínimo de 80% esperado para garantir que a suíte de testes exerce efetivamente a lógica do código. Mutantes sobreviventes indicam código não testado ou asserts fracos que não detectam alterações de comportamento.

## What Changes

- **Novos testes unitários** para funções/métodos que hoje não possuem cobertura de teste, focando nos 886 mutantes sobreviventes agrupados por módulo
- **Fortalecimento de asserts** em testes existentes que cobrem o código mas não são sensíveis o suficiente para detectar mutações (ex: mocks que validam apenas que a chamada ocorreu, sem verificar argumentos específicos)
- **Adição de padrões ao `do_not_mutate_patterns`** do mutmut para mutações impossíveis de matar com testes unitários (ex: strings de formatação de log, mensagens de exceção, argumentos de subprocess mockados)
- Ordem de trabalho: módulos de prioridade alta primeiro (clipboard_image, cache, generators, calendar, repository, strategies), depois prioridade média (parser, client, use_cases), depois baixa (CLI, presentation)

## Capabilities

### New Capabilities
- `mutation-coverage`: Testes adicionais que matam mutantes sobreviventes identificados pelo mutmut, elevando o mutation score de 61.95% para >= 80%

### Modified Capabilities
<!-- Nenhuma capacidade existente tem seus requisitos alterados - apenas testes são adicionados -->

## Impact

- Arquivos de teste em `tests/test_infrastructure/`, `tests/test_domain/`, `tests/test_application/`
- Configuração `pyproject.toml` (seção `[tool.mutmut]`) para adicionar padrões ao `do_not_mutate_patterns`
- Nenhuma alteração em código de produção (`src/`)
- Nenhuma quebra de API ou mudança de comportamento
