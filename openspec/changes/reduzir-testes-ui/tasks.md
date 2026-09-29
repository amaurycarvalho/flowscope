<!-- Ordenação: esta change DEVE ser aplicada antes de `bloquear-ui-inicializacao`.
     Aquela adiciona um teste `@needs_display` do overlay; com o baseline em 250
     (sem folga) e o ratchet "só encolhe", o +1 reprovaria o guardrail. Se já
     houver redução aplicada aqui, o overlay pode consumir a folga. -->

## 1. Baseline e guardrail do teto de UI

- [ ] 1.1 Extrair o baseline da constante `BASELINE_NEEDS_DISPLAY` entregue por A em `tests/architecture/test_ui_test_budget.py` (valor corrente **250**) para `tests/architecture/ui_test_budget.txt` e fazer o guardrail lê-lo, verificando com teste que o arquivo é a fonte do teto
- [ ] 1.2 Completar o guardrail (A já entregou a reprovação por aumento) com o **ratchet**: uma queda da contagem exige a atualização explícita do baseline, com testes sintéticos de incremento (reprova) e de queda (exige atualização)
- [ ] 1.3 Definir o critério objetivo de teste de UI (cria `tk.Tk`/`Toplevel` ou é gated por `DISPLAY`) na varredura AST e verificar que testes headless não contam para o teto

## 2. Migrar lógica pura para as camadas internas

- [ ] 2.1 Verificar a migração de `TestPreview` já entregue por A em `tests/test_application/test_document_preview.py` (roda sem `DISPLAY`) e confirmar que não restou lógica pura equivalente em `tests/test_presentation`
- [ ] 2.2 Revisar os demais módulos de UI em busca de testes de lógica de `application`/`domain` e migrá-los, confirmando que `tests/test_presentation` deixa de conter lógica pura

## 3. Converter processamento para headless

- [ ] 3.1 Converter preview em thread, cache de texto e aplicação de resumo do painel de documentos para testes headless via fakes de mixin/manager e verificar equivalência de comportamento
- [ ] 3.2 Converter os testes de leitura de catálogo/séries e de lote do painel de notícias para headless
- [ ] 3.3 Converter os testes de integração de evolução dos fundamentos que só exercitam processamento para headless
- [ ] 3.4 Confirmar que os fluxos de job/orquestração cobertos por A/B/C são testados sem Tk (A já converteu fundamental/resumos; B/C convertem a carga e as leituras) e baixar o baseline
- [ ] 3.5 Converter os testes de envio/cancelamento do `ChatPanel` — transporte portado por `cache-prompt-chat` (manager local, grupo `"chat"`, `latest_wins`, `Confirmacao`) — para um fake de manager headless, preservando paridade de mensagens, estados de botão e histórico, e baixar o baseline

## 4. Consolidar testes de widget

- [ ] 4.1 Mapear testes de estado de widget/botão duplicados e manter um representante por comportamento observável (habilitação, empty-state, wiring), removendo redundâncias
- [ ] 4.2 Baixar o baseline após cada rodada de consolidação e verificar que a suíte de apresentação permanece verde

## 5. Reconciliar specs e verificação final

- [ ] 5.1 Adicionar os deltas de `layer-boundaries` e `presentation-test-coverage` e validar o change
- [ ] 5.2 Rodar a suíte completa, a checagem de fronteiras, o guardrail de teto e o teste de complexidade, confirmando que a contagem de testes de UI caiu e não há perda de comportamento observável
