# Indicadores Calculados pelo FlowScope

## Categoria: Preço

### Range (Amplitude)
- **ID:** `range`
- **Descrição:** Amplitude absoluta da oscilação do ativo no pregão.
- **Fórmula:** `Máxima − Mínima`
- **Aplicabilidade:** Mede a volatilidade intradiária do ativo. Valores elevados indicam maior dispersão de preços.

### Range Percentual
- **ID:** `range_percentual`
- **Descrição:** Amplitude do dia normalizada pelo preço médio.
- **Fórmula:** `Range / PreçoMédio`
- **Aplicabilidade:** Permite comparar a volatilidade entre ativos de diferentes patamares de preço. Útil para rankear volatilidade relativa.

### Typical Price (Preço Típico)
- **ID:** `typical_price`
- **Descrição:** Média simples dos preços máximo, mínimo e fechamento.
- **Fórmula:** `(Máxima + Mínima + Fechamento) / 3`
- **Aplicabilidade:** Referência de preço de equilíbrio do pregão. Usado como proxy do preço médio negociado em análises sintéticas.

### Median Price (Preço Mediano)
- **ID:** `median_price`
- **Descrição:** Ponto médio da faixa de preços do dia.
- **Fórmula:** `(Máxima + Mínima) / 2`
- **Aplicabilidade:** Medida de tendência central do intervalo de preços, ignorando o viés do fechamento.

### Weighted Close (Fechamento Ponderado)
- **ID:** `weighted_close`
- **Descrição:** Média que atribui peso duplo ao preço de fechamento.
- **Fórmula:** `(Máxima + Mínima + 2 × Fechamento) / 4`
- **Aplicabilidade:** Suaviza o fechamento contra os extremos do dia. Útil para identificar viés de fechamento em relação à faixa de negociação.

---

## Categoria: Fluxo Financeiro

### CLV — Close Location Value
- **ID:** `clv`
- **Descrição:** Posição do fechamento dentro da faixa de preços do dia, variando de −1 a +1.
- **Fórmula:** `((Fechamento − Mínima) − (Máxima − Fechamento)) / (Máxima − Mínima)`
- **Aplicabilidade:** −1 indica fechamento no pior preço do dia (pressão vendedora máxima); +1 indica fechamento no melhor preço (pressão compradora máxima). Revela direcionalidade intradiária.

### Money Flow Multiplier (Multiplicador de Fluxo Financeiro)
- **ID:** `money_flow_multiplier`
- **Descrição:** Aliás do CLV. Mesmo cálculo e interpretação.
- **Fórmula:** Idêntica ao CLV.
- **Aplicabilidade:** Usado como insumo para o cálculo do Money Flow Volume. Nomenclatura语义 para análise de fluxo de ordens.

### Buying Pressure (Pressão Compradora)
- **ID:** `buying_pressure`
- **Descrição:** Fração do range que representa o movimento comprador (do piso até o fechamento).
- **Fórmula:** `(Fechamento − Mínima) / (Máxima − Mínima)`
- **Aplicabilidade:** Varia de 0 a 1. Próximo de 1 indica que o fechamento ocorreu próximo à máxima, sugerindo dominância compradora ao longo do dia.

### Selling Pressure (Pressão Vendedora)
- **ID:** `selling_pressure`
- **Descrição:** Fração do range que representa o movimento vendedor (do fechamento até o teto).
- **Fórmula:** `(Máxima − Fechamento) / (Máxima − Mínima)`
- **Aplicabilidade:** Complementar à Buying Pressure (soma = 1). Próximo de 1 indica fechamento próximo à mínima, sugerindo dominância vendedora.

### Money Flow Volume (Volume de Fluxo Financeiro)
- **ID:** `money_flow_volume`
- **Descrição:** Volume financeiro acumulado ponderado pelo sinal do Money Flow Multiplier.
- **Fórmula:** `Σ(MFM × VolumeFinanceiro)` para todos os dias do período.
- **Aplicabilidade:** Valor positivo indica fluxo líquido comprador no período; negativo indica fluxo líquido vendedor. Útil para identificar acúmulo ou distribuição.

---

## Categoria: Tamanho de Negócios

### Average Trade Size (Ticket Médio em Quantidade)
- **ID:** `average_trade_size`
- **Descrição:** Quantidade média de instrumentos por negócio.
- **Fórmula:** `QuantidadeTotal / NúmeroDeNegócios`
- **Aplicabilidade:** Valores elevados sugerem participação institucional (grandes blocos). Valores baixos sugerem predominância de investidores de varejo.

### Average Financial Ticket (Ticket Médio Financeiro)
- **ID:** `average_financial_ticket`
- **Descrição:** Valor financeiro médio por negócio.
- **Fórmula:** `VolumeFinanceiro / NúmeroDeNegócios`
- **Aplicabilidade:** Similar ao ticket médio em quantidade, mas em termos monetários. Auxilia na detecção de fluxo institucional vs. varejo.

---

## Categoria: Volume

### VWAP — Volume-Weighted Average Price
- **ID:** `vwap`
- **Descrição:** Preço médio ponderado pelo volume de instrumentos negociados no período.
- **Fórmula:** `Σ(PreçoMédio × Quantidade) / Σ(Quantidade)`
- **Aplicabilidade:** Referência de preço justo (fair value) do período. Utilizado como linha de suporte/resistência dinâmica. Desvios do VWAP indicam regiões de sobrecompra/sobrevenda intradiária.

### Volume Profile (Perfil de Volume)
- **ID:** `volume_profile`
- **Descrição:** Distribuição do volume financeiro em buckets de preço (tick a tick) entre mínima e máxima do ativo.
- **Fórmula:** Volume financeiro distribuído uniformemente em faixas de preço de tamanho igual ao tick size (R$ 0,01).
- **Aplicabilidade:** Visualizado como gráfico de violino. Revela regiões de maior concentração de volume (alta liquidez) e gaps de preço com baixa atividade.

### Top Tickers (Principais Ativos)
- **ID:** `top_tickers`
- **Descrição:** Seleciona os N ativos com maior volume financeiro acumulado no período.
- **Fórmula:** Agregação de `NtlFinVol` por ticker, ordenação decrescente, filtro dos N primeiros (padrão = 15).
- **Aplicabilidade:** Utilizado como filtro padrão de tickers para análise quando nenhuma lista é fornecida. Foca a análise nos ativos mais líquidos.

---

## Categoria: Eficiência

### Daily Efficiency (Eficiência Diária)
- **ID:** `daily_efficiency`
- **Descrição:** Mede quanto do range do dia foi convertido em deslocamento líquido de preço (do preço médio ao fechamento).
- **Fórmula:** `|Fechamento − PreçoMédio| / Range`
- **Aplicabilidade:** Próximo de 0 indica um dia lateral (price oscillates but returns). Próximo de 1 indica um dia direcional forte (todo o range foi usado para movimento líquido). Útil para identificar convicção direcional.

---

## Categoria: Densidade

### Financial Density (Densidade Financeira)
- **ID:** `financial_density`
- **Descrição:** Volume financeiro negociado por unidade de variação de preço.
- **Fórmula:** `VolumeFinanceiro / Range`
- **Aplicabilidade:** Quanto maior o valor, mais intensa foi a atividade financeira em relação à oscilação de preço. Picos indicam alta liquidez concentrada em pequenas faixas de preço.

### Trade Density (Densidade de Negócios)
- **ID:** `trade_density`
- **Descrição:** Número de negócios realizados por unidade de variação de preço.
- **Fórmula:** `QuantidadeDeNegócios / Range`
- **Aplicabilidade:** Indica a intensidade de negociação (fragmentação). Valores altos sugerem grande número de ordens em faixas estreitas de preço, típico de momentos de indecisão ou microestrutura ativa.

### Volume Density (Densidade de Volume)
- **ID:** `volume_density`
- **Descrição:** Quantidade de instrumentos negociados por unidade de variação de preço.
- **Fórmula:** `QuantidadeDeInstrumentos / Range`
- **Aplicabilidade:** Mede a concentração de volume em relação à oscilação. Complementa a densidade financeira, mas em termos de quantidade de ativos (livre do efeito preço).

---

## Campos do CSV de Pregão (B3 — TradeInformationConsolidated)

| Coluna no CSV | Campo no `TradeDay` | Tipo | Descrição |
|---|---|---|---|
| `RptDt` | `date` | `date` | Data do pregão (formato ISO ou brasileiro) |
| `TckrSymb` | `ticker` | `Ticker` | Código de negociação do ativo (ticker) |
| `SgmtNm` | `segment` | `str` | Nome do segmento de listagem (ex.: CASH). Usado como filtro nos dados |
| `MinPric` | `min_price` | `Price` | Menor preço negociado no dia |
| `MaxPric` | `max_price` | `Price` | Maior preço negociado no dia |
| `TradAvrgPric` | `avg_price` | `Price` | Preço médio ponderado dos negócios realizados |
| `LastPric` | `last_price` | `Price` | Último preço negociado (fechamento) |
| `TradQty` | `trades_qty` | `Volume` | Quantidade total de negócios realizados no dia |
| `NtlFinVol` | `fin_vol` | `Decimal` | Volume financeiro total negociado (R$) |
| `FinInstrmQty` | `fin_instr_qty` | `int` | Quantidade total de instrumentos negociados |
