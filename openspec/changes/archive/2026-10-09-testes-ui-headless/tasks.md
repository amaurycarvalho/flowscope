<!-- Fatiado por vetor (ver design.md Decisão 5). Cada fase termina baixando
     tests/architecture/ui_test_budget.txt (o ratchet exige atualização
     explícita) e com a suíte de apresentação verde. Partida: 225. -->

## 1. Fase matplotlib — separar figura/canvas

- [x] 1.1 Refatorar `FundamentalEvolutionPanel` para expor a montagem/atualização do `Figure`/`Axes` independente do `Frame`/`FigureCanvasTkAgg`/toolbar, deixando a casca Tk como invólucro fino; verificar a suíte atual verde e que a figura pode ser construída com `Figure()` pura sem `DISPLAY`
- [x] 1.2 Converter para headless os testes de eixo, título, ticks, tooltip, estado vazio e cópia de `tests/test_presentation/test_fundamental_evolution_panel.py` (operando sobre `Figure`/`Axes`), manter um smoke test da casca Tk e baixar o baseline para o valor medido, verificando o guardrail `test_ui_test_budget`
- [x] 1.3 Refatorar `CorrelationNetworkPanel` no mesmo padrão (figura pura separada do canvas/toolbar); verificar a suíte atual verde e instanciação sem `DISPLAY`
- [x] 1.4 Converter para headless os testes de render/posições/colorbar/aviso/estado vazio de `tests/test_presentation/test_correlation_network_panel.py`, mantendo gated apenas toolbar e toolbar-visível, e baixar o baseline verificando o guardrail

## 2. Fase documento — decisões puras e host DocumentFlowMixin

- [x] 2.1 Expor em `DocumentFlowMixin`/`DocumentTreePanel` decisões como valores puros (ex.: `resumir_habilitado()`, `abrir_habilitado()`) e fazer os widgets apenas consumirem o resultado, verificando a suíte atual verde
- [x] 2.2 Converter `TestRefreshResumirButton`, `TestBotaoResumirDuranteLote` e `TestBotaoAbrir` para verificar as decisões headless, mantendo um smoke test de binding de estado por botão, e baixar o baseline verificando o guardrail
- [x] 2.3 Cobrir `render_grupo`/`mensagem_indisponivel` de `charts/document_grouping.py` diretamente (headless) e converter `TestAgrupamento`/`TestMensagemIndisponibilidade`, removendo a duplicação via Tk, e baixar o baseline verificando o guardrail
- [x] 2.4 Converter `TestAplicarResumo`, `TestPersistenciaNoWorkerDoPainel`, `TestEstadoVazioERefresh` e `TestAcquireCallback` para um host headless de `DocumentFlowMixin` (padrão de `test_document_preview_flow.py`), preservando a asserção de texto/estado, e baixar o baseline verificando o guardrail

## 3. Fase config LLM — modelo de formulário

- [x] 3.1 Extrair de `llm/config_dialog.py` um modelo de formulário puro (carga, presets, provedor ativo, decisão salvar/ativar), deixando o diálogo só ligando `StringVar` ao modelo e verificando a suíte atual verde
- [x] 3.2 Converter `TestCargaESalvamento` e `TestConfigPorProvedor` para headless sobre o modelo, mantendo gated modal (`resizable`/`grab`), máscara de chave e o fluxo de teste de conexão em thread, e baixar o baseline verificando o guardrail

## 4. Fase botões/notícias — reuso de fakes existentes

- [x] 4.1 Converter `TestDisableIdempotente`, `TestDisableDocumentosBotoes`, `TestBotaoInterromper` e os testes de cursor de `tests/test_presentation/test_button_state.py` usando o padrão `_FakeWidget`/`_CursorHost` já existente, mantendo gated apenas ponteiro/layout real, e baixar o baseline verificando o guardrail
- [x] 4.2 Converter os testes de construção/seleção/resumo do `NoticiasPanel` que só exercitam `DocumentFlowMixin` e seções para headless (host com fakes), preservando estado vazio e texto observável, e baixar o baseline verificando o guardrail

## 5. Reconciliar specs e verificação final

- [x] 5.1 Confirmar o delta de `openspec/specs/presentation-test-coverage/spec.md` (contrato de costura testável) e validar o change com `openspec validate testes-ui-headless` (verde; o aviso RFC-2119 em inglês é esperado, dado o uso de `DEVE` no padrão do repo)
- [x] 5.2 Rodar a suíte completa (`pytest`), o guardrail de teto, a checagem de fronteiras e o teste de complexidade, confirmando baseline reduzido, ausência de aumentos e paridade de comportamento observável
