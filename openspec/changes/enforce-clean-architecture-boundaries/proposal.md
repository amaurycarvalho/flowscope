## Why

O guardrail de fronteira ainda mantém três violações legadas de
`presentation -> infrastructure` na allowlist (`app_about_actions.py`,
`app_actions.py` e `llm/config_dialog.py`). O change `clean-architecture-layering`
define que a allowlist DEVE encolher e ficar vazia no incremento de fechamento, e
que `presentation` só pode importar `infrastructure` no composition root. Esta
fatia remove essas três dívidas via portas de `application` injetadas pelo
composition root e zera a allowlist.

## What Changes

- A verificação de nova versão (`obter_ultima_release`) sai de
  `presentation/gui/app_about_actions.py` para uma porta de `application`,
  consumida pelo mixin via injeção; a comparação de versões passa pela
  aplicação (usando `domain.version.is_newer`).
- O diálogo de LLM (`presentation/gui/llm/config_dialog.py`) deixa de importar
  `infrastructure.llm.config`/`factory` e passa a receber uma porta de
  configuração de LLM de `application` (presets, leitura/gravação, deps e
  criação do provedor).
- A cópia de gráfico (`presentation/gui/app_actions.py`) deixa de importar
  `infrastructure.clipboard_image` e passa a receber uma porta de clipboard de
  `application`, com o erro de clipboard declarado na aplicação.
- O composition root (`presentation/cli.py`, `presentation/main.py` e
  `presentation/gui/app_wiring.py`) constrói os adaptadores de infraestrutura e
  injeta as portas nos painéis/Diálogo; continua sendo a única exceção a
  `presentation -> infrastructure`.
- A allowlist de fronteira (`tests/architecture/allowlist.txt`) é zerada; o
  teste de fronteira passa a exigir zero violações e zero entradas.
- Criação de testes puros em `tests/test_application` para as portas/casos de
  uso e adaptação dos testes de apresentação para os fakes injetados.
- Sem alteração de comportamento observável: os atalhos, o diálogo de
  configuração e a cópia de gráfico permanecem idênticos.

## Capabilities

### New Capabilities

### Modified Capabilities

Opta por não alterar specs (`skip_specs: true`): refatoração de fronteira que
preserva o comportamento observável, implementando o cenário "Fechamento zera a
allowlist" do contrato `layer-boundaries` do change `clean-architecture-layering`.

## Impact

- **Depende de**: todos os increments anteriores de `clean-architecture-layering`
  (allowlist reduzida às 3 entradas legadas) e de `add-layer-architecture-guardrails`.
- **Código afetado**: `presentation/gui/app_about_actions.py`,
  `presentation/gui/app_actions.py`, `presentation/gui/llm/config_dialog.py` e o
  composition root (`app_wiring.py`/`app.py`); novas portas/casos de uso em
  `application`.
- **Código novo**: portas de `application` para releases, configuração de LLM e
  clipboard, com adaptadores em `infrastructure` ligados no composition root.
- **Testes**: allowlist zerada e guardrail verde; novos testes puros de
  aplicação; testes de apresentação ajustados para as dependências injetadas.
- **Sem alteração de comportamento**: versão exibida, persistência da
  configuração, teste de conexão, avisos e cópia de gráfico permanecem iguais.
