## 1. Levantamento e estrutura do guardrail

- [x] 1.1 Levantar as violações atuais de fronteira (imports proibidos por camada) e registrar a lista na allowlist; verificar que a contagem bate com a auditoria deste change
- [x] 1.2 Criar o teste de fronteira generalizado para `domain`, `application`, `infrastructure` e `presentation`, reaproveitando o padrão `ast` de `tests/test_domain/test_fii/test_layer_boundaries.py`; verificar que ele roda em `tests/architecture/`
- [x] 1.3 Aplicar a tabela de regras por camada (quem pode importar quem) conforme `layer-boundaries`; verificar com um caso conhecido de cada regra

## 2. Allowlist decrescente

- [x] 2.1 Implementar a comparação allowlist x violações: violação nova reprova e entrada obsoleta também reprova; verificar com teste de violação sintética
- [x] 2.2 Marcar os pontos de composição (`presentation/gui/app_wiring.py`, `presentation/main.py`, `presentation/cli.py`) como a única exceção `presentation -> infrastructure`; verificar que o restante de `presentation` não importa `infrastructure`

## 3. Documentação e integração

- [x] 3.1 Documentar a convenção de view-model e o uso da allowlist como referência para os increments filhos; verificar que a referência está acessível no change chapéu
- [x] 3.2 Rodar `make test` e `make quality-gate` e confirmar tudo verde com a allowlist populada
