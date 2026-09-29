## Context

Ver `proposal.md - Why`. O `tests/architecture` já usa o padrão de allowlist que "só encolhe" (`allowlist.txt` + `guardrail.py` + `test_layer_boundaries.py`). O gating de UI é feito por um `@needs_display` por arquivo (definido em cada módulo) e não há verificação agregada. As fatias A/B/C deixam a orquestração de background no `BackgroundManager`, o que torna a maior parte do processamento testável com fakes headless.

A fatia A já materializou uma **primeira fatia** deste escopo: `tests/architecture/test_ui_test_budget.py` conta `@needs_display` e reprova aumento contra a constante `BASELINE_NEEDS_DISPLAY = 250`; `TestPreview` já foi migrado para `tests/test_application`; e os testes de coreografia de jobs (fundamental/resumos) já foram reduzidos a trabalho puro. A change `cache-prompt-chat` portou o envio do chat para um `BackgroundManager` local ao painel (grupo `"chat"`, `latest_wins`), de modo que a orquestração do chat (submissão, cancelamento, descarte do desfecho tardio) também é exercitável com um fake de manager, sem Tk. Esta change parte desse estado e completa o desenho.

## Goals / Non-Goals

**Goals:**
- Reduzir a contagem de testes `@needs_display` ao mínimo que só existe com Tk.
- Tornar a redução verificável e impedir regressão (teto que só encolhe).
- Reconciliar `presentation-test-coverage` com o comportamento pós-A/B/C.

**Non-Goals:**
- Perseguir meta numérica de cobertura ou substituir testes de mutação.
- Remover testes de comportamento observável para "bater a meta"; a redução vem de onde não há comportamento de UI.
- Alterar código de `src/` (salvo pequenos seams já previstos em A/B/C para permitir o teste headless).

## Decisions

### Decisão 1: Baseline commitado com teto que só encolhe

**Escolha**: `tests/architecture/ui_test_budget.txt` guarda a contagem baseline de testes com gating de display; o guardrail compara e reprova aumento, exigindo atualização do baseline para valores menores.

**Alternativas**: marcador `pytest` com contagem reportada sem falha; meta em prosa.

**Razão**: replica um padrão já usado e confiável no repositório (`allowlist.txt`), é barato e torna a regressão impossível por descuido.

**Reconciliação com A**: A entregou o guardrail com a constante `BASELINE_NEEDS_DISPLAY = 250` embutida em `tests/architecture/test_ui_test_budget.py`, que só reprova aumento. Esta change:

- extrai o valor para `tests/architecture/ui_test_budget.txt`, inicializado em **250**, e faz o guardrail lê-lo (mesmo padrão do `allowlist.txt`);
- adiciona o **ratchet**: contagem menor que o baseline reprova e exige a atualização do arquivo para o valor novo (o teto só encolhe);
- aproveita o ponto de partida já reduzido por A; o baseline inicial desta change é 250 (não ~253).

**Coordenação com `bloquear-ui-inicializacao`**: a contagem corrente é **exatamente 250**, sem folga. Como aquele change adiciona um teste `@needs_display` para o overlay e o ratchet aqui proíbe aumento, esta change DEVE ser aplicada primeiro (ou já ter baixado o baseline) antes daquele; alternativamente, o baseline deve ser explicitamente atualizado para acomodar o overlay, decisão que quebra a intenção "só encolhe" e por isso é evitada.

### Decisão 2: Critério objetivo de "teste de UI"

**Escolha**: conta para o teto um teste que cria `tk.Tk`/`Toplevel` ou é decorado com gating de `DISPLAY`. Testes de processamento usam fakes de mixin/presenter/manager e não criam Tk.

**Alternativas**: classificar por diretório.

**Razão**: o diretório não distingue (há muitos testes headless em `tests/test_presentation`); o comportamento — exigir display — é o critério que importa para o custo e para o orçamento.

### Decisão 3: Migrar lógica pura para as camadas internas

**Escolha**: testes de lógica de `application`/`domain` que hoje vivem em módulos de UI migram para `tests/test_application`/`tests/test_domain`.

**Alternativas**: mantê-los onde estão, apenas removendo o gating.

**Razão**: além de sair do teto, a localização correta é exigida pelo spec `layer-boundaries` ("lógica pura testada sem display") e facilita a descoberta.

**Reconciliação com A**: o caso exemplar (`TestPreview`) já foi migrado por A para `tests/test_application/test_document_preview.py`; esta change apenas verifica essa migração e procura ocorrências remanescentes.

### Decisão 4: Consolidar testes de widget duplicados

**Escolha**: manter um teste representativo por comportamento observável de widget (habilitação, empty-state, wiring), removendo variações redundantes que não distinguem comportamento.

**Alternativas**: manter todos.

**Razão**: o orçamento pede o mínimo estritamente necessário; duplicatas de estado não agregam cobertura de comportamento. A verificação de mutação permanece como rede de segurança.

### Decisão 5: Reconciliar a cobertura com o comportamento pós-A/B/C

**Escolha**: o delta de `presentation-test-coverage` exige verificação headless do processamento e restringe a UI ao que só existe com Tk; o delta de `layer-boundaries` adiciona o teto enforced.

**Razão**: sem isso, o teto não tem âncora normativa e a cobertura continuaria descrevendo o modelo síncrono.

### Decisão 6: Transporte do chat coberto headless

**Escolha**: os testes do `ChatPanel` que exercitam o ciclo do job de envio — `TestCancelarEnvio` (desfecho tardio, falha tardia, novo envio após cancelar) e o despacho de `Confirmacao` — passam a usar um `BackgroundManager` fake (ou o manager real com `_AgendadorFake`, como em `test_background_manager.py`), sem instanciar `tk.Tk`. Permanecem sob UI apenas o estado dos botões, a exibição da conversa e a existência do campo somente-leitura.

**Alternativas**: manter os testes gated acessando `painel._background.jobs_ativos[0].thread`.

**Razão**: `cache-prompt-chat` tornou o envio um job de manager com token por job e política `latest_wins`; o cancelamento e o descarte do desfecho tardio são lógica de manager (já coberta headless em `TestConfirmacao`), não comportamento de widget. É a mesma regra de `presentation-test-coverage`: processamento sem Tk, UI restrita ao widget.

## Risks / Trade-offs

- **[Risco]** Cobertura efetiva cair ao converter/remover testes → **Mitigação**: preservar o teste de mutação e exigir que cada comportamento convertido tenha equivalente headless; paridade observável como critério de aceite.
- **[Risco]** Baseline frágil, mudando a cada refatoração → **Mitigação**: o guardrail exige atualização explícita do baseline; a queda é bem-vinda e o aumento é bloqueado.
- **[Risco]** Classificação errônea de um teste como headless → **Mitigação**: o critério da Decisão 2 é objetivo (cria Tk/gate); o guardrail detecta por AST.
- **[Risco]** `bloquear-ui-inicializacao` adicionar um `@needs_display` sem folga no baseline (250/250) e o ratchet reprovar → **Mitigação**: aplicar esta change antes daquela ou baixar o baseline antes de introduzir o overlay.
- **[Trade-off]** Conversão em massa gera um diff grande de testes → **Benefício**: suíte mais rápida, determinística e alinhada ao orçamento.

## Migration Plan

1. Verificar o que A já entregou (guardrail de aumento, `TestPreview`, orquestração de jobs headless) e registrar o baseline inicial em `tests/architecture/ui_test_budget.txt` com o valor corrente **250**.
2. Migrar testes de lógica pura para `tests/test_application`/`tests/test_domain`.
3. Converter para headless os testes de processamento restantes nos módulos de UI.
4. Consolidar testes de widget duplicados e baixar o baseline a cada passo (o ratchet exige a atualização explícita).
5. Atualizar os deltas de `layer-boundaries` e `presentation-test-coverage`; rodar a suíte de apresentação, a checagem de fronteiras e o teste de mutação; rollback = reverter os commits (apenas testes e specs).
