## Context

Ver `proposal.md` — Why, e o contrato em `openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md`. O repositório já tem um teste de fronteira feito à mão (`tests/test_domain/test_fii/test_layer_boundaries.py`) que percorre arquivos com `ast` e detecta imports de camadas externas. O guardrail generaliza esse mecanismo para todas as camadas e adiciona a allowlist das violações atuais.

## Goals / Non-Goals

**Goals:**

- Detectar import proibido entre camadas em qualquer subpacote, com uma allowlist explícita e versionada.
- Falhar em import novo fora do permitido; permanecer verde enquanto as violações legadas existirem.
- Servir de critério objetivo para cada incremento remover entradas da allowlist.

**Non-Goals:**

- Não implementar os movimentos de código (responsabilidade dos increments filhos).
- Não usar ferramentas externas de arquitetura (import-linter, pytest-archon); manter dependência zero e o padrão `ast` já usado.
- Não analisar imports dinâmicos/condicionais dentro de funções além do que o `ast` cobre hoje.

## Decisions

### D1 — Teste próprio com `ast`, reaproveitando o padrão existente

Generaliza a varredura de `test_layer_boundaries.py` para os pacotes `domain`, `application`, `infrastructure` e `presentation`, com uma tabela de regras por camada (quem pode importar quem). Alternativa: `import-linter` (dependência nova e configuração em arquivo à parte). Rejeitada para manter o padrão já testado no projeto e evitar dependência de quality gate.

### D2 — Allowlist como dado versionado, não como `xfail`

Um arquivo (por exemplo `tests/architecture/allowlist.txt` ou constante Python) lista violações legadas como `camada_origem:modulo -> camada_destino`. O teste compara o conjunto de violações encontradas com a allowlist: violação nova reprova; entrada da allowlist sem violação correspondente também reprova (força encolher ao mover). Alternativa: marcar violações como `xfail`. Rejeitada porque `xfail` não força a remoção e esconde a dívida.

### D3 — Composition root com exceção explícita

Os pontos de composição (`presentation/gui/app_wiring.py`, `presentation/main.py`, `presentation/cli.py`) são a única exceção `presentation -> infrastructure` e ficam listados na allowlist até o fechamento. Alternativa: permitir qualquer import sob `presentation/gui/app_*.py`. Rejeitada por ser ampla demais e não forçar a isolar o ponto de composição.

### D4 — Convenção de view-model apenas documentada

A convenção (aplicação devolve dataclasses; apresentação formata/desenha) é registrada como referência para os increments; não é verificável por `ast` de forma confiável, então não vira teste rígido. Alternativa: lint de proibição de acesso a `all_indicators`/`daily_data` em `presentation`. Rejeitada por falso-positivo elevado.

## Risks / Trade-offs

- [Allowlist virar depósito permanente] → a entrada só permanece enquanto a violação existir; o teste reprova allowlist obsoleta e o fechamento exige lista vazia.
- [Falso-negativo em imports indiretos] → o guardrail cobre imports estáticos (suficiente para o padrão do projeto); revisão cobre o resto.
- [Nuance de `__init__.py` que reexporta] → varrer os arquivos de módulo (não só os `__init__`) e resolver o alvo do import pelo prefixo, como faz o teste atual.

## Migration Plan

1. Criar o teste generalizado e a allowlist com o levantamento atual das violações (27 imports `presentation -> infrastructure` fora do wiring + regras de domínio em `presentation` + entidades em `infrastructure`), todos permitidos.
2. Rodar `make test` e confirmar verde.
3. Cada incremento filho remove suas entradas; o fechamento zera a lista.

Rollback: remover o teste e a allowlist restaura o estado anterior sem efeito no produto.

## Open Questions

- Formato exato da allowlist (arquivo `.txt` vs constante Python): decidir na implementação, sem impacto no contrato.
