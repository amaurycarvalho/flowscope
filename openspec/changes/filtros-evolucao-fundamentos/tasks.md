## 1. Seleção de datas (camada de aplicação)

- [x] 1.1 Em `application/fundamental/evolucao.py`, adicionar a janela parametrizada (`periodo_dias` + âncora com fallback para a observação mais recente) e verificar com testes de unidade cobrindo janela normal, janela vazia e sem observações
- [x] 1.2 Implementar `selecionar_datas_fibonacci_reverso` (espelho do atual) preservando extremos e regra de `≤2` observações, e verificar com testes de unidade
- [x] 1.3 Implementar `selecionar_datas_fibonacci_duplo` (3 alvos do caminho recente + 3 do antigo + centro, deduplicado) e verificar com testes de unidade
- [x] 1.4 Implementar `selecionar_datas_monte_carlo` (extremos + intermediárias aleatórias com `random.Random(semente)`; 5 e 12 intermediárias) e verificar estabilidade entre chamadas com a mesma semente
- [x] 1.5 Implementar o dispatcher `selecionar_datas(disponiveis, metodo, *, semente=None)` cobrindo todos os métodos, incluindo "Todos os dias", e verificar com testes de unidade
- [x] 1.6 Simplificar `montar_series` para não amostrar (apenas mapear observações recebidas) e verificar que os testes existentes de `TestMontarSeries` continuam passando

## 2. Job de leitura e ações

- [x] 2.1 Atualizar `evolucao_job.preparar_series` para receber `periodo_dias`, `metodo` e `ancora`, aplicar a seleção e filtrar as observações, e verificar com testes de `TestPrepararSeries`
- [x] 2.2 Em `app_actions._update_fundamental_evolution`, ler `get_sampling_config()`/`_data_referencia()`, repassar a config a `preparar_series` e incluir `(ticker, periodo, metodo)` na `chave` do job, e verificar com testes de apresentação
- [x] 2.3 Atualizar `_aplicar_evolucao` para descartar resultados cujo ticker ou configuração tenha mudado, e verificar com teste de resultado obsoleto
- [x] 2.4 Manter `_update_fundamental_evolution` funcionando no caminho síncrono (sem `_background`), e verificar com teste dedicado

## 3. Painel e gatilhos de interface

- [x] 3.1 Fazer `_on_period_combo_changed` e `_on_sampling_combo_changed` remontarem o painel quando a sub-aba estiver visível, inclusive sem dados B3, e verificar com teste de gatilho
- [x] 3.2 Atualizar o título do painel para informar as datas exibidas em relação ao período, e verificar com teste do painel
- [x] 3.3 Atualizar os textos de orientação (`panels.md` e `TAB_CONTENT` da sub-aba) para descrever período e amostragem configuráveis, e verificar que os testes de conteúdo de aba passam

## 4. Verificação integrada

- [x] 4.1 Executar a suíte de testes de aplicação e apresentação e verificar que passa
- [x] 4.2 Executar lint e typecheck do projeto e verificar que não há erros
- [x] 4.3 Validar a mudança com `openspec validate filtros-evolucao-fundamentos` e verificar que retorna "is valid"
