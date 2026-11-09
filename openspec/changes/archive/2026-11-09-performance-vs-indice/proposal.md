# Proposal

## Why

Hoje o FlowScope compara ativos entre si (VWAP, Quadrantes, Dominância e Rede), mas não responde se um ativo performou melhor ou pior que o seu índice de referência no período. Sem essa comparação, o usuário não consegue separar o movimento do ativo do movimento do mercado nem avaliar o excesso de retorno em pontos percentuais. A funcionalidade entra na release 1.8.0.

## What Changes

- Nova sub-aba **"Performance"** na "Análise Geral", posicionada entre "Dominância do Pregão" e "Rede de Correlação".
- Gráfico de **barras de excesso de retorno acumulado** (`retorno do ticker − retorno do índice`), em pontos percentuais, com o zero representando o índice: barras positivas indicam desempenho acima do índice e negativas, abaixo.
- **Combobox de benchmark** com IFIX, IBOV e IDIV, filtrado pelos tipos de ativo presentes: IFIX só aparece se houver FII; IBOV e IDIV só aparecem se houver ação. Default: primeiro ticker FII → IFIX; primeiro ticker ação → IBOV.
- Apenas tickers do tipo correspondente entram no gráfico: FII no IFIX; ação no IBOV/IDIV. ETF, BDR e tipo desconhecido ficam fora.
- Respeito aos **combos globais de período e amostragem**, com recálculo automático ao alterá-los.
- **Ingestão automática** da série diária de fechamento dos índices na pipeline de atualização, usando o endpoint B3 `indexStatisticsProxy/IndexCall/GetPortfolioDay` (JSON por ano), com cache por índice e ano.
- **Bases de retorno**: IBOV = preço; IFIX e IDIV = total (proventos reinvestidos na data ex derivada da data-com). IDIV Price Return fica fora da 1.8.0.
- **Cache pré-calculado** dos resultados por índice, data de referência, período, amostragem, conjunto de tickers e base de retorno.
- **Limitação registrada**: sem ajuste de split, grupamento, desdobramento ou bonificação. Quando um evento do tipo for detectável por heurística, o painel avisa que o retorno pode estar distorcido.
- Barra de ferramentas idêntica à do VWAP (Início, Voltar, Avançar, Mover, Ampliar, Salvar e Copiar Gráfico).
- Release **1.8.0**.

## Capabilities

### New Capabilities

- `performance-index-panel`: sub-aba Performance, gráfico de excesso de retorno, combobox de benchmark, regras de elegibilidade por tipo de ativo, cálculo do retorno relativo, cache de resultados, limitação documentada e aviso de evento societário suspeito.

### Modified Capabilities

- `data-ingestion`: nova ingestão e cache da série diária de fechamento dos índices da B3 (IBOV, IDIV e IFIX), além das carteiras já suportadas.

## Impact

- `infrastructure/b3/client.py`, `infrastructure/b3/parser.py` e `infrastructure/b3/repository.py`: download e parsing do endpoint `indexStatisticsProxy/IndexCall/GetPortfolioDay` e cache por `(índice, ano)`.
- `application/ports.py`: novo contrato para obtenção da série histórica do índice.
- `application/performance/`: cálculo puro do excesso de retorno, alinhamento de datas e heurística de evento suspeito.
- Pipeline de carga (`application/use_cases.py` e controlador): coleta da série do índice e cálculo/cache dos resultados.
- `presentation/gui/app_tab_layout.py`, `app_layout.py` e `app_tabs.py`: registro da sub-aba, do painel e do texto de orientação.
- `presentation/gui/charts/performance_panel.py`: novo painel matplotlib com a `ToolbarBR`.
- Testes de aplicação, infraestrutura e apresentação; `docs/misc/panels.md`, `docs/misc/datasources.md` e CHANGELOG/release.
- Nenhuma dependência externa nova; apenas uma nova URL/endpoint da B3 já utilizada como datasource.
