## Context

Ver `proposal.md` — Why, e os contratos em
`openspec/changes/clean-architecture-layering/specs/layer-boundaries/spec.md` e
`tests/architecture/guardrail.py`. Estado atual relevante:

- O guardrail (`tests/architecture/test_layer_boundaries.py` + `guardrail.py`)
  já cobre todas as camadas e isenta o composition root
  (`presentation/cli.py`, `presentation/main.py`,
  `presentation/gui/app_wiring.py`).
- A allowlist tem exatamente 3 violações legadas:
  `presentation/gui/app_about_actions.py -> infrastructure` (`obter_ultima_release`),
  `presentation/gui/app_actions.py -> infrastructure` (`copy_image_to_clipboard`,
  `ClipboardError`) e `presentation/gui/llm/config_dialog.py -> infrastructure`
  (`config.py`/`factory.py`).
- `app_wiring.py` já concentra a construção dos adaptadores de infraestrutura e é
  composition root; `app.py` combina os mixins e é onde a injeção pode ser
  registrada.
- O diálogo de LLM é criado sob demanda em
  `presentation/gui/app_tab_actions.py::_abrir_config_llm`.
- `AboutActionsMixin._consultar_versao_publicada` usa `domain.version.is_newer`
  (domínio) e `obter_ultima_release` (infraestrutura).
- `ActionsMixin._copy_chart` importa `clipboard_image` dentro do método, no
  caminho quente de cópia de gráfico.
- Todos os increments anteriores de `clean-architecture-layering` foram
  implementados; restam apenas estas 3 entradas para zerar a allowlist.

## Goals / Non-Goals

**Goals:**

- Remover as 3 violações legadas via portas de `application` injetadas pelo
  composition root, zerando a allowlist.
- Garantir que `presentation` só importe `infrastructure` no composition root.
- Cobrir as novas portas/casos de uso com testes puros em `tests/test_application`.

**Non-Goals:**

- Não alterar comportamento observável (versão, configuração da LLM, teste de
  conexão, avisos e cópia de gráfico).
- Não mover a implementação de I/O de `infrastructure` (HTTP de releases,
  leitura/gravação de config, clipboard) — apenas expô-la por portas.
- Não mudar a definição de composition root nem as regras de camadas do
  `guardrail.py`.
- Não converter os testes de UI existentes além do necessário para injetar os
  fakes.

## Decisions

### D1 — Verificação de versão por porta de `application`

Cria-se em `application` a porta `ReleaseChecker` (com `obter_ultima_release()`)
e a função `verificar_nova_versao(versao_atual, checker)` que aplica
`domain.version.is_newer` e devolve `(versao, url)` apenas quando houver versão
mais nova. O `infrastructure/releases/client.py` permanece; o composition root
injeta o checker (`GitHubReleaseChecker`/função adaptada) no `AboutActionsMixin`.
A apresentação deixa de importar `infrastructure` e `is_newer`. Alternativa:
tratar o check como composition root e chamá-lo de `main.py`. Rejeitada por
espalhar regra de "há versão nova" fora da aplicação.

### D2 — Configuração de LLM por porta de `application`

Cria-se `LLMConfigPort` em `application` com `get_presets`,
`load_provider_configs`, `load_llm_config`, `save_llm_config`, `check_llm_deps`,
`create_provider(config)` e `default_config()`. Um adaptador em
`infrastructure/llm/` implementa a porta sobre `config.py` e `factory.py`.
`LLMConfigDialog` passa a receber a porta no construtor; o composition root a
fornece a `app_tab_actions._abrir_config_llm`, que a repassa ao diálogo. O
`DEFAULT_LLM_CONFIG["rpm"]` passa a vir de `default_config()`. `LLMError`
continua vindo de `domain`. Alternativa: mover a leitura da config para a
apresentação. Rejeitada por ser I/O persistente.

### D3 — Clipboard por porta de `application`

Cria-se `ImageClipboardPort` (`copy_image(figure)`) e a exceção
`ClipboardError` em `application`. O adaptador em `infrastructure` envolve
`copy_image_to_clipboard` e traduz a exceção de infraestrutura para a da
aplicação. `ActionsMixin._copy_chart` usa a porta injetada e captura a exceção de
aplicação. Alternativa: manter o import local sob justificativa de caminho
quente. Rejeitada por ainda caracterizar violação `presentation -> infrastructure`.

### D4 — Composition root como única exceção e allowlist vazia

Os adaptadores são construídos e injetados em `presentation/gui/app_wiring.py`
(ou `app.py`, a partir do que ele expõe); `cli.py`/`main.py` seguem como
composition root. `tests/architecture/allowlist.txt` fica vazio (apenas o
cabeçalho explicativo), e o teste de fronteira passa a exigir
`find_violations() == set()` e nenhuma entrada obsoleta. Alternativa: remover o
arquivo e a leitura da allowlist. Rejeitada por manter o mecanismo disponível e
o teste de duplicatas/obsoletas.

### D5 — Testes puros das portas e adaptadores

Criam-se testes em `tests/test_application` para `verificar_nova_versao`,
`LLMConfigPort` (com um fake de armazenamento) e `ImageClipboardPort` (com um
fake do sistema), sem `DISPLAY`. Os testes de apresentação
(`test_about_tab`, `test_controller`, `test_main`, `test_llm_config_dialog`)
passam a injetar fakes das portas no lugar dos imports de infraestrutura.
Alternativa: testar apenas via UI. Rejeitada pelo orçamento de testes de UI.

## Risks / Trade-offs

- [Injeção em mixins por herança múltipla] → registrar as portas em `app.py`
  antes de qualquer ação e dar defaults seguros (portas opcionais) para não
  quebrar testes que instanciam mixins isolados.
- [Diálogo criado sob demanda] → `app_tab_actions` lê a porta de `self`
  (injetada na composição) e a repassa; ausência da porta cai num adaptador
  padrão construído no composition root.
- [Tradução de erros do clipboard] → a porta declara `ClipboardError` na
  aplicação; o adaptador converte a exceção de infraestrutura, preservando a
  mensagem exibida.
- [Allowlist vazia quebra o teste de obsoletas] → remover as entradas e o
  cabeçalho orienta a não readicionar; o guardrail acusa qualquer regressão.
- [Regressão de comportamento na config da LLM] → manter as assinaturas e os
  textos; cobrir leitura/gravação e deps com testes puros.

## Migration Plan

1. Criar as portas de `application` (releases, LLM config, clipboard) e os
   adaptadores de `infrastructure`.
2. Injetar as portas na GUI pelo composition root (`app_wiring.py`/`app.py`).
3. Atualizar `app_about_actions.py`, `app_actions.py` e
   `llm/config_dialog.py` para consumirem as portas, sem imports de
   `infrastructure`.
4. Esvaziar a allowlist e ajustar/verificar o teste de fronteira.
5. Criar/ajustar testes puros e de UI.
6. Rodar `make test` e `make quality-gate` (guardrail incluso) com allowlist
   vazia.

Rollback: reverter o change restaura os imports diretos e as entradas da
allowlist; comportamento idêntico.

## Open Questions

- Onde declarar as portas (módulo único `application/ports_*` vs arquivos por
  assunto) e se os adaptadores são classes ou funções: decidir na implementação,
  sem impacto no contrato.
- Forma de injeção nos mixins (atributos definidos em `app.py` vs construtor):
  decidir na implementação, preservando os defaults seguros.
