## Context

O FlowScope usa mutmut para mutation testing. A execução atual (`make mutation-results`) gerou um log em `mutants/mutmut-cicd-results.log` com 886 mutantes sobreviventes de 2,493 totais (score 61.95%). O target é >= 80%.

A suíte de testes existente cobre o código em grande parte (coverage >= 85%), mas muitos testes usam mocks que validam apenas `assert_called_once()` sem verificar argumentos específicos, permitindo que mutações em parâmetros sobrevivam.

O trabalho é organizado em ordem de prioridade: módulos menores com alto retorno primeiro, progredindo para os mais complexos.

## Goals / Non-Goals

**Goals:**
- Elevar o mutation score de 61.95% para >= 80%
- Escrever testes unitários adicionais que matem mutantes sobreviventes
- Fortalecer asserts em testes existentes para detectar mutações em argumentos
- Adicionar padrões ao `do_not_mutate_patterns` para mutações impossíveis de matar com teste unitário
- Seguir ordem módulo a módulo, priorizando maior ROI

**Non-Goals:**
- NÃO alterar código de produção (`src/`)
- NÃO rodar mutmut (será feito manualmente pelo usuário)
- NÃO fazer commit no git
- NÃO escrever testes de integração reais (manter testes unitários com mocks)

## Decisions

### Decisão 1: Ordem de ataque - Módulos de alta prioridade primeiro

**Escolha**: Começar por módulos pequenos e autocontidos com muitos survivors (clipboard_image, cache, generators, calendar), depois expandir.

**Alternativa**: Atacar logo o maior módulo (use_cases, 144 survivors). Rejeitado porque módulos menores dão feedback mais rápido e constroem confiança.

**Rationale**: Cada módulo tem seu próprio arquivo de teste. Trabalhar módulo a módulo permite validação incremental com `pytest tests/test_infrastructure/test_<module>.py` sem rodar a suíte inteira a cada iteração.

### Decisão 2: Mutantes impossíveis de matar → `do_not_mutate_patterns`

**Escolha**: Adicionar padrões ao `do_not_mutate_patterns` no `pyproject.toml` para mutações que não podem ser mortas com teste unitário.

**Alternativa**: Escrever testes de integração reais. Rejeitado porque exigiria infraestrutura externa (B3 API, xclip, etc.) e está fora do escopo.

**Categorias a adicionar**:
- Strings específicas de formato de data (`%Y-%m-%d`, `%y-%m-%d`, etc.) — sobrevivem porque o mock não valida o formato
- Nomes de parâmetros em dicionários internos (ex: `cached_at`, `tickers` em payloads JSON)
- Sufixos de arquivo (`.tmp`, `.TMP`) — comportamento equivalente

### Decisão 3: Estratégia por categoria de mutação

| Categoria | Estratégia |
|-----------|-----------|
| String literal (arg names, keys) | Adicionar assert sobre o valor exato no mock |
| Parâmetro default (bool→None) | Assert que o argumento foi passado com o valor esperado |
| Constante numérica | Teste parametrizado cobrindo boundary values |
| Operador lógico (and→or, ==→!=) | Teste que exercita o branch oposto |
| Remoção de argumentos | Assert que a chamada inclui todos os argumentos esperados |

### Decisão 4: Não rodar mutmut

**Escolha**: Validar cada mudança apenas com `pytest` no arquivo de teste modificado.

**Rationale**: O usuário fará a execução completa do mutmut manualmente após todas as alterações. Rodar mutmut a cada módulo seria redundante e lento.

## Risks / Trade-offs

- **[Risk] Testes podem passar mas não matar o mutante** → Mitigação: Verificar manualmente o diff do mutante no log para garantir que o novo teste exercita a mutação específica
- **[Risk] `do_not_mutate_patterns` pode ser muito agressivo** → Mitigação: Só adicionar padrões quando for comprovadamente impossível matar com teste unitário; revisar cada adição
- **[Trade-off] Testes com assertions mais rigorosas são mais frágeis** → Aceitável, pois o propósito é justamente detectar mudanças de comportamento
- **[Risk] Alterar `pyproject.toml` pode conflitar com outras mudanças** → Mitigação: Fazer alteração mínima, apenas na seção `[tool.mutmut]`
