## 1. Baseline e guardrail do teto de UI

- [ ] 1.1 Registrar em `tests/architecture/ui_test_budget.txt` a contagem atual de testes com gating de display e verificar que o arquivo é lido pelo guardrail
- [ ] 1.2 Implementar o teste arquitetural que compara a contagem corrente ao baseline e reprova aumento, com teste sintético de que o incremento falha e a queda exige atualização
- [ ] 1.3 Definir o critério objetivo de teste de UI (cria `tk.Tk`/`Toplevel` ou é gated por `DISPLAY`) na varredura AST e verificar que testes headless não contam para o teto

## 2. Migrar lógica pura para as camadas internas

- [ ] 2.1 Migrar `TestPreview` (`texto_de_html`, `texto_preview`, `tem_texto`) de `tests/test_presentation` para `tests/test_application` e verificar que roda sem `DISPLAY`
- [ ] 2.2 Revisar os demais módulos de UI em busca de testes de lógica de `application`/`domain` e migrá-los, confirmando que `tests/test_presentation` deixa de conter lógica pura

## 3. Converter processamento para headless

- [ ] 3.1 Converter preview em thread, cache de texto e aplicação de resumo do painel de documentos para testes headless via fakes de mixin/manager e verificar equivalência de comportamento
- [ ] 3.2 Converter os testes de leitura de catálogo/séries e de lote do painel de notícias para headless
- [ ] 3.3 Converter os testes de integração de evolução dos fundamentos que só exercitam processamento para headless
- [ ] 3.4 Confirmar que os fluxos de job/orquestração cobertos por A/B/C são testados sem Tk e baixar o baseline

## 4. Consolidar testes de widget

- [ ] 4.1 Mapear testes de estado de widget/botão duplicados e manter um representante por comportamento observável (habilitação, empty-state, wiring), removendo redundâncias
- [ ] 4.2 Baixar o baseline após cada rodada de consolidação e verificar que a suíte de apresentação permanece verde

## 5. Reconciliar specs e verificação final

- [ ] 5.1 Adicionar os deltas de `layer-boundaries` e `presentation-test-coverage` e validar o change
- [ ] 5.2 Rodar a suíte completa, a checagem de fronteiras, o guardrail de teto e o teste de complexidade, confirmando que a contagem de testes de UI caiu e não há perda de comportamento observável
