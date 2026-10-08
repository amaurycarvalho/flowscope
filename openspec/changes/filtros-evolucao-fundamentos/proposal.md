## Why

A sub-aba "Evolução dos Fundamentos" ignora os comboboxes da barra superior: lê todo o histórico retido (365 dias) e aplica sempre a mesma amostragem Fibonacci fixa. O usuário não consegue restringir a janela (30/60/90 dias) nem escolher o estilo de amostragem para compor os gráficos de timeseries, tornando o painel inconsistente com o restante do app.

## What Changes

- A Evolução dos Fundamentos passa a montar as séries a partir do **período** (30/60/90 dias) e do **método de amostragem** selecionados nos comboboxes da barra superior.
- A janela é ancorada na data de referência atual; se ela não contiver observações, a âncora recua para a observação mais recente do cache. A origem continua sendo exclusivamente o cache histórico, sem aquisição de rede.
- Cada método (Fibonacci, Fibonacci reverso, Fibonacci duplo, Monte Carlo, Monte Carlo duplo, Todos os dias) seleciona um subconjunto das observações presentes no cache dentro da janela, preservando o contrato atual: extremos sempre presentes, `≤2` observações devolvem todas, sem datas inventadas, ordem crescente e sem duplicatas.
- **BREAKING (spec-level):** o requisito "Amostragem Fibonacci das datas" deixa de ser fixo e passa a depender da configuração selecionada; novo requisito de janela de período.
- Monte Carlo passa a ter amostra determinística por `(ticker, janela, método, n)` para o gráfico não "pular" a cada render.
- Mudar qualquer um dos comboboxes re-renderiza o painel mesmo sem dados B3 carregados.
- Título do painel passa a informar as datas exibidas em relação ao total do período.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `fundamental-evolution-panel`: a amostragem das datas deixa de ser Fibonacci fixa e passa a respeitar o período e o método selecionados; adiciona o requisito de janela de período e cenários por método.

## Impact

- `application/fundamental/evolucao.py`: seleção de datas parametrizada (janela + método) e `montar_series` recebendo as datas selecionadas.
- `presentation/gui/evolucao_job.py`: `preparar_series` recebe `periodo`, `metodo` e `ancora`.
- `presentation/gui/app_actions.py`: lê `get_sampling_config()` e `_data_referencia()`, propaga a config para a leitura em background e inclui a config na `chave`/guard de obsolescência.
- `presentation/gui/app_layout.py` / `app_tab_actions.py`: mudança de combobox dispara o re-render do painel.
- Testes de `test_application/test_fundamental_evolucao.py`, `test_presentation/test_fundamental_evolution_integration.py`, `test_leituras_catalogo_background.py`.
