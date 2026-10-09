## Context

Ver `proposal.md - Why`. A primeira onda (`reduzir-testes-ui`, arquivada) entregou o guardrail `tests/architecture/test_ui_test_budget.py` com baseline commitado em `tests/architecture/ui_test_budget.txt` (atual: **225**) e o ratchet "o teto só encolhe". O spec `presentation-test-coverage` já exige verificação headless do processamento; o spec `layer-boundaries` já exige o teto verificado e a paridade de comportamento.

O que resta não é wiring, e sim lógica presa ao widget por ausência de costura, em três formas:

1. Painéis matplotlib (`fundamental_evolution_panel`, `correlation_network_panel`) constroem `Figure`/`Axes` (puro) e `FigureCanvasTkAgg`/toolbar (Tk) no mesmo `__init__`. Os testes de título, eixos, tooltip, cor/posição e estado vazio só exigem Tk por causa do canvas.
2. Mixins (`DocumentFlowMixin`, `StatusMixin`) derivam decisões (habilitar "Resumir pendentes", "Abrir documento", estado de cancelamento) e aplicam-nas diretamente via `widget.config(...)`, sem expor o resultado.
3. `llm/config_dialog.py` mistura carga/presets/provedor ativo com `StringVar` do Tk.

Já existem, no próprio repositório, os padrões headless que serão reaplicados: host que herda o mixin e troca os seams por fakes (`test_document_preview_flow.py`), `__new__(Classe)` + MagicMock, e `Figure()` pura (`test_fundamental_evolution_panel.py::test_titulo_informa_datas_no_periodo`).

## Goals / Non-Goals

**Goals:**
- Expor costuras em `src/` que tornem headless a verificação da lógica não-Tk dos painéis citados, sem alterar comportamento.
- Converter as declarações gated correspondentes e baixar o baseline (ratchet).
- Deixar sob UI apenas o que só existe com Tk.

**Non-Goals:**
- Meta numérica de cobertura ou remoção de teste por teste "para bater a meta".
- Reescrever a arquitetura de background/jobs (já feita em A/B/C).
- Alterar a saída observável (rótulos, textos, números, ordem).
- Converter `fundamental_table` em massa: a montagem de linhas já vive em `application/fundamental/linhas.py` e é coberta headless.

## Decisions

### Decisão 1: Separar construção de figura do invólucro Tk

**Escolha**: o painel de gráfico passa a ter a montagem/atualização de `Figure`/`Axes` acessível sem Tk; o `Frame` + `FigureCanvasTkAgg` + toolbar ficam como casca fina que embute a figura.

**Alternativas**: marcar os testes matplotlib como `@pytest.mark.slow`; migrar para `tests/test_application` sem mudar `src/`.

**Razão**: a única dependência de Tk é o canvas. Separar as duas responsabilidades permite `Figure()` pura (backend Agg), é o caminho já provado por `test_titulo_informa_datas_no_periodo`, e remove o gate da lógica sem mover a responsabilidade de apresentação para `application`. Marcar como slow não reduz o orçamento; migrar para application violaria `layer-boundaries` (apresentação é desenho).

### Decisão 2: Expor decisões de mixin como valores puros

**Escolha**: mixins devolvem o booleano/decisão (ex.: `resumir_habilitado()`, `abrir_habilitado()`) e o widget apenas consome; os testes verificam o valor, mantendo **um** smoke test de binding por botão.

**Alternativas**: continuar testando `widget.cget("state")`; extrair um "view-model" separado.

**Razão**: mesma regra do spec — processamento sem Tk, UI restrita ao widget. Extrair um view-model completo é excesso para o tamanho do ganho; o booleano mais o smoke test cobre o comportamento observável sem perder a fiação.

### Decisão 3: Modelo de formulário para o diálogo de configuração

**Escolha**: extrair de `LLMConfigDialog` a lógica de carga, presets, provedor ativo e decisão de salvar/ativar (esta última já tem `deve_ativar`/`assinatura_conexao` puros) para um objeto/estrutura sem Tk; o diálogo só liga `StringVar` ao modelo.

**Alternativas**: manter os testes acessando `_provider_var.get()`.

**Razão**: a leitura/escrita de `StringVar` só existe por causa do Tk; o conteúdo (dict de config, presets) é puro e já é parcialmente puro (`TestAssinaturaConexao`, `TestDeveAtivar`). Permite testar dicas de preset, restauração por provedor e máscara de chave sem root.

### Decisão 4: Fakes headless como padrão de conversão

**Escolha**: converter usando host que herda o mixin e troca os seams por fakes (padrão de `test_document_preview_flow.py`) ou `__new__(Classe)` + MagicMock (padrão de `TestReClickDocumentos`). Não introduzir novo utilitário de teste além do necessário.

**Alternativas**: criar um framework de fakes genérico.

**Razão**: os dois padrões já estão no repositório, são reconhecíveis e evitam duplicação de infraestrutura; `test-infra-mocking` já cobre a base de mocking.

### Decisão 5: Ordem dos vetores por ganho/esforço

**Escolha**: aplicar por fases, do maior retorno por risco:

```
  1. matplotlib (fundamental_evolution, correlation_network)  ~25
  2. documento (decisoes puras + render_grupo + host)          ~25-30
  3. llm_config_dialog (modelo de formulario)                  ~12
  4. button_state (host _FakeWidget ja existente)              ~10
  5. noticias_panel (host DocumentFlowMixin)                   ~8
```

**Razão**: 1 e 2 concentram o maior número de declarações com costura mecânica/ja provada. 5 reusa o mesmo mecanismo de 2, então vem depois de estabilizado.

### Decisão 6: Ratchet e paridade como critério de aceite

**Escolha**: cada fase baixa `ui_test_budget.txt` explicitamente e exige suíte verde; paridade observável é verificada mantendo a asserção de comportamento (textos/números/ordem) no novo teste headless ou em teste de application equivalente.

**Alternativa**: baixar o baseline só no final.

**Razão**: o ratchet atual reprova qualquer queda não registrada, então a atualização é obrigatória por fase; fazê-lo incrementalmente mantém o sinal do guardrail útil durante o trabalho e evita um commit gigante opaco.

## Risks / Trade-offs

- **[Risco] Perda de cobertura ao converter** → Mitigação: cada conversão preserva a asserção de valor/paridade; onde havia só `cget("state")`, manter um smoke test de binding; mutação permanece como rede.
- **[Risco] Matplotlib exigir display** → Mitigação: usar `Figure()` pura (backend Agg), sem importar `backend_tkagg` no caminho testado; a casca Tk importa o backend.
- **[Risco] Baseline frágil a cada fase** → Mitigação: queda exige atualização explícita (ratchet); aumento é bloqueado.
- **[Risco] Migrar responsabilidade de apresentação para `application`** → Mitigação: a costura mantém a lógica na apresentação; não mover desenho para application.
- **[Risco] Conversão ampla gerar diff grande e difícil de revisar** → Mitigação: fatiar por fase/vetor, cada uma com baseline e suíte verde.
- **[Trade-off] A casca Tk fica levemente maior** para embutir a figura → Benefício: lógica testável deterministicamente e suíte mais rápida.

## Migration Plan

1. Fase matplotlib: separar figura/canvas nos dois painéis; converter os testes de eixo/tooltip/estado vazio; baixar o baseline.
2. Fase documento: expor decisões puras de `DocumentFlowMixin`/painel; testar `render_grupo` e mensagens direto; usar host headless para resumo/preview; baixar o baseline.
3. Fase config LLM: extrair modelo de formulário; converter carga/preset/provedor; baixar o baseline.
4. Fase botões/notícias: reusar `_FakeWidget` e o host `DocumentFlowMixin`; baixar o baseline.
5. Atualizar o delta de `presentation-test-coverage`; rodar suíte completa, guardrail de teto e teste de complexidade. Rollback = reverter os commits (testes, seams de `src/` e baseline).

## Open Questions

- Nenhuma que altere spec, abordagem ou tarefas. A meta exata de baseline por fase é ajustada conforme a contagem medida (o ratchet a exige explícita).
