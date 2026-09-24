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

### Daily Money Flow (Fluxo Financeiro Diário)
- **ID:** `daily_money_flow`
- **Descrição:** Fluxo financeiro diário ponderado pelo sinal do CLV.
- **Fórmula:** `CLV × VolumeFinanceiro` por data.
- **Dependência:** Depende do indicador `clv`.
- **Aplicabilidade:** Diferente do Money Flow Volume (que acumula), este é calculado por data. Valor positivo indica fluxo comprador líquido naquele pregão; negativo indica fluxo vendedor. É o indicador principal do painel Fluxo Financeiro (sub-aba "Análise do Ticker"), onde aparece em milhões de reais no card de classificação ao lado do score normalizado. Também utilizado como traço horizontal no gráfico de evolução da dominância.

### Dominance Score (Score de Dominância)
- **ID:** `dominance_score`
- **Descrição:** Combina direção do fechamento (CLV) com a convicção do movimento (Daily Efficiency).
- **Fórmula:** `CLV × DailyEfficiency` por data.
- **Dependências:** Depende dos indicadores `clv` e `daily_efficiency`.
- **Aplicabilidade:** Valores positivos altos indicam forte dominância compradora com alta convicção; valores negativos baixos indicam forte dominância vendedora. Valores próximos de zero sugerem indecisão ou movimento lateral, independentemente da direção do CLV.

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

### VWAP Distance (Desvio do VWAP)
- **ID:** `vwap_distance`
- **Descrição:** Desvio percentual do último preço negociado em relação ao VWAP diário (TradAvrgPric).
- **Fórmula:** `(LastPric − TradAvrgPric) / TradAvrgPric`
- **Dependência:** Depende do indicador `vwap` (utiliza o `daily_vwap` de cada data como denominador).
- **Aplicabilidade:** Mede se o fechamento de cada dia ocorreu acima (valor positivo) ou abaixo (valor negativo) do preço médio ponderado negociado naquele dia. Valores positivos indicam viés comprador no fechamento; negativos, viés vendedor. Útil como coordenada Y no gráfico de quadrantes e para identificar distorções de preço relativas ao valor justo do dia.

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

## Categoria: Fundamentalista

Métricas usadas na tabela de Fundamentos (aba "Análise Geral") e na Evolução dos Fundamentos (aba "Análise do Ticker"). Os valores são calculados com precisão decimal completa e arredondados somente na apresentação; `N/A` indica ausência do dado.

### Valor de Mercado
- **ID:** `market_value`
- **Descrição:** Valor de mercado do ativo.
- **Fórmula:** `Cotação × Nº de cotas/ações emitidas`
- **Aplicabilidade:** Base para o Dividend Yield, o FFO Yield e o P/FFO; dimensiona o ativo.

### Preço Típico (52 semanas)
- **ID:** `preco_tipico`
- **Descrição:** Referência de preço médio de 52 semanas.
- **Fórmula:** `(Máxima 52s + Mínima 52s + Cotação) / 3`
- **Aplicabilidade:** Referência para o P / PT e para identificar prêmio/desconto da cotação frente ao histórico.

### P / PT (Cotação sobre Preço Típico)
- **ID:** `p_pt`
- **Descrição:** Desconto (negativo) ou prêmio (positivo) da cotação frente ao Preço Típico.
- **Fórmula:** `(Cotação − Preço Típico) / Preço Típico`

### P/L (Preço/Lucro)
- **ID:** `p_l`
- **Descrição:** Quantos anos de lucro (ou dividendo) são necessários para recuperar o preço.
- **Fórmula:** ações — valor reportado pela fonte; FIIs — `Cotação / (Último dividendo × 12)`; BDRs — `Cotação / (Último dividendo × 4)`.
- **Aplicabilidade:** No FII o dividendo mensal é anualizado (× 12) para expressar anos, como no P/L de uma ação; no BDR, o dividendo trimestral é anualizado (× 4).

### P/VP (Preço/Valor Patrimonial)
- **ID:** `p_vp`
- **Descrição:** Relação entre o valor de mercado e o patrimônio líquido.
- **Fórmula:** `Valor de Mercado / Patrimônio Líquido`
- **Aplicabilidade:** Abaixo de 1 indica cota negociando abaixo do patrimônio.

### Dividend Yield
- **ID:** `dividend_yield`
- **Descrição:** Rendimento dos dividendos acumulados em 12 meses sobre o valor de mercado.
- **Fórmula:** `Dividendos (12m) / Valor de Mercado`

### Último Dividendo e Tendência
- **ID:** `ultimo_dividendo`, `dividendo_anterior`, `tendencia_dividendo`
- **Descrição:** Último dividendo (tipo Rendimento), o anterior e a tendência entre eles.
- **Fórmula:** `(Último − Anterior) / Anterior`
- **Aplicabilidade:** Faixas: Forte Alta (≥ +5%), Leve Alta (> 0), Estável (= 0), Leve Queda (≥ −5%) e Forte Queda (< −5%). Sem dividendo anterior a tendência é `N/A`.

### FFO/Receita (12m e 3m)
- **ID:** `ffo_receita_12m`, `ffo_receita_3m`
- **Descrição:** Fração da receita convertida em caixa operacional (FFO).
- **Fórmula:** `FFO / Receita`
- **Aplicabilidade:** Receita ou FFO negativos exibem texto de motivo em vez de número; insumo ausente ou receita zero exibem `N/A`.

### Dividendos/Receita (12m e 3m)
- **ID:** `dividendos_receita_12m`, `dividendos_receita_3m`
- **Descrição:** Fração da receita destinada a dividendos.
- **Fórmula:** `Dividendos / Receita`

### Dividendos/FFO (12m e 3m)
- **ID:** `dividendos_ffo_12m`, `dividendos_ffo_3m`
- **Descrição:** Quanto do caixa operacional é consumido pelos dividendos.
- **Fórmula:** `Dividendos / FFO`
- **Aplicabilidade:** Abaixo de 100% o FFO cobre os dividendos; acima de 100% os dividendos superam o FFO; negativo indica FFO negativo no período.

### FFO Trend
- **ID:** `ffo_trend`
- **Descrição:** Tendência do FFO/Receita comparando a janela de 3 meses com a de 12 meses.
- **Fórmula:** `FFO/Receita (3m) − FFO/Receita (12m)`
- **Aplicabilidade:** Faixas em pontos percentuais: Forte Alta (≥ +20 p.p.), Leve Alta (≥ +5 p.p.), Estável, Leve Queda (≥ −20 p.p.) e Forte Queda (< −20 p.p.).

### FFO Yield
- **ID:** `ffo_yield`
- **Descrição:** Rendimento do caixa operacional sobre o valor de mercado.
- **Fórmula:** `FFO (12m) / Valor de Mercado`

### P/FFO
- **ID:** `p_ffo`
- **Descrição:** Múltiplo do caixa operacional sobre o valor de mercado.
- **Fórmula:** `Valor de Mercado / FFO (12m)`

### FFO Momentum
- **ID:** `ffo_momentum`
- **Descrição:** Variação do FFO recente anualizado frente ao FFO de 12 meses.
- **Fórmula:** `(FFO (3m) × 4) / FFO (12m) − 1`

### Shorts% (Short Interest sobre o free float)
- **ID:** `shorts_pct`
- **Descrição:** Fração do *free float* (ações em circulação) que está alugada e ainda não foi devolvida; mede a magnitude relativa da aposta baixista.
- **Fórmula:** `Ações Alugadas / Free Float`
- **Aplicabilidade:** O *free float* vem do CVM FRE (`Quantidade_Total_Acoes_Circulacao`); na sua ausência, o denominador é o total emitido (ações/cotas) e, para FIIs, o total de cotas. Insumo ausente ou denominador zero exibem `N/A`; apresentado em percentual com uma casa decimal. Também é exibido como série temporal na Evolução dos Fundamentos (aba "Análise do Ticker").

### Volume de Shorts
- **ID:** `volume_shorts`
- **Descrição:** Classificação qualitativa da magnitude do Shorts%.
- **Fórmula:** Classificação categórica do `Shorts%` (ver tabela em Classificações Qualitativas).
- **Aplicabilidade:** `Inexistente` para `0%` ou `N/A`; `Muito Baixo` (< 1%); `Baixo` (< 3%); `Alto` (≤ 10%); `Muito Alto` (> 10%).

### Fechamento Shorts (SIR — Short Interest Ratio)
- **ID:** `sir`
- **Descrição:** Número de dias necessários para que os vendedores a descoberto recomprem as ações alugadas ao volume médio diário de negociação; mede a dificuldade operacional de fechamento.
- **Fórmula:** `Ações Alugadas / Volume Médio Diário de Negociação`
- **Aplicabilidade:** O volume médio é a média do `fin_instr_qty` dos dias disponíveis em memória. Sem dias, volume médio zero ou ações alugadas ausentes exibem `N/A`; apresentado em dias, com uma casa decimal e sufixo `d` (ex.: `5,0d`).

### Risco Fechamento
- **ID:** `risco_fechamento`
- **Descrição:** Classificação qualitativa da dificuldade de fechamento (risco de *short squeeze*).
- **Fórmula:** Classificação categórica do `SIR` (ver tabela em Classificações Qualitativas).
- **Aplicabilidade:** `Inexistente` para `0` ou `N/A`; `Muito Baixo` (< 2); `Baixo` (< 4); `Alto` (≤ 5); `Muito Alto` (> 5).

### Classes de Cotistas e de Patrimônio
- **ID:** `classe_cotistas`, `classe_patrimonio`
- **Descrição:** Classificação determinística do nº de cotistas/acionistas e do tamanho do patrimônio.
- **Aplicabilidade:** Cotistas: Micro (≤ 250), Muito Pequeno (≤ 1.000), Pequeno (≤ 5.000), Médio (≤ 35.000), Grande (≤ 65.000), Muito Grande (≤ 100.000) e Gigante (> 100.000). Patrimônio: Micro (< R$ 50 mi), Pequeno (≤ R$ 100 mi), Médio (≤ R$ 250 mi), Grande (≤ R$ 500 mi), Muito Grande (≤ R$ 1 bi) e Gigante (> R$ 1 bi).

---

## Contexto do Chat com I.A.

O chat não calcula indicadores novos: ele reaproveita os indicadores e dados já produzidos pelo FlowScope como contexto para a LLM. A aba "Chat AI" monta esse contexto em três origens, além de um ponto de extensão para fontes adicionais.

### Conhecimento do FlowScope
- **Origem:** textos de orientação das sub-abas (`TAB_CONTENT`) e informações da aba "Sobre" (apresentação, licença e versão).
- **Aplicabilidade:** responde perguntas sobre o próprio aplicativo e sobre como interpretar cada painel; enviado como bloco de sistema estável.

### Fundamentos carregados
- **Origem:** a mesma tabela da sub-aba "Fundamentos" (análise fundamentalista por ticker).
- **Serialização:** uma linha por ticker com os valores não vazios no formato `[TICKER] Coluna=valor; ...`.
- **Escopo:** watchlist completa; o ticker referido é inferido pela LLM a partir do texto da pergunta, que pede esclarecimento quando a pergunta for ambígua quanto ao ativo.

### Documentos em cache
- **Resumos:** os `short_summary` (até 280 caracteres) e `long_summary` (até 1.500 caracteres) da sub-aba "Documentos", lidos por `DocumentCatalog`/`JsonDocumentSummaryStore`.
- **Texto integral:** lido de `document-texts/` (`JsonDocumentTextStore`) apenas para os documentos-alvo pedidos pela LLM, após o gate de confirmação por quantidade.
- **Preparação sob demanda:** quando o texto ou o resumo não estão em cache, são preparados reutilizando a extração de HTML/PDF e o `ResumirDocumentoUseCase`.

### Fontes adicionais
- **Origem:** ponto de extensão `ContextoChat.fontes_adicionais`, com provedores que recebem a pergunta e devolvem um título e um texto.
- **Aplicabilidade:** changes futuras (notícias em `noticias-b3`, recuperação vetorial em `llm-chat-rag`) registram as suas fontes; cada uma é renderizada como seção própria, sem alterar a ordem da cascata de documentos. Fonte que falha ou retorna vazio é omitida, sem impedir a resposta.

### Orçamento de contexto
- **Teto por documento:** 12.000 caracteres (mesmo precedente do resumidor).
- **Teto global:** 40.000 caracteres.
- **Excedente:** truncado com aviso registrado no log.

---

## Classificações Qualitativas

Rótulos derivados dos indicadores para uso nos painéis e no card de classificação.

### Dominância (por CLV)
| Faixa de CLV | Classificação |
|---|---|
| < −0,70 | Venda Muito Forte |
| −0,70 a −0,40 | Venda Forte |
| −0,40 a −0,15 | Venda Moderada |
| −0,15 a +0,15 | Equilíbrio |
| +0,15 a +0,40 | Compra Moderada |
| +0,40 a +0,70 | Compra Forte |
| ≥ +0,70 | Compra Muito Forte |

### Convicção (por Eficiência Diária)
| Faixa de Eficiência | Classificação |
|---|---|
| < 0,20 | Muito Baixa |
| 0,20 a 0,40 | Baixa |
| 0,40 a 0,60 | Moderada |
| 0,60 a 0,80 | Alta |
| ≥ 0,80 | Muito Alta |

### Fluxo Financeiro (por Score normalizado)
| Faixa de Score | Classificação |
|---|---|
| < −0,15 | Fluxo Muito Forte (Vendedor) |
| −0,15 a −0,08 | Fluxo Forte (Vendedor) |
| −0,08 a −0,03 | Fluxo Moderado (Vendedor) |
| −0,03 a −0,01 | Fluxo Fraco (Vendedor) |
| −0,01 a +0,01 | Neutro |
| +0,01 a +0,03 | Fluxo Fraco (Comprador) |
| +0,03 a +0,08 | Fluxo Moderado (Comprador) |
| +0,08 a +0,15 | Fluxo Forte (Comprador) |
| ≥ +0,15 | Fluxo Muito Forte (Comprador) |

### Volume de Shorts (por Shorts%)
| Faixa de Shorts% | Classificação |
|---|---|
| 0% ou N/A | Inexistente |
| > 0% e < 1% | Muito Baixo |
| ≥ 1% e < 3% | Baixo |
| ≥ 3% e ≤ 10% | Alto |
| > 10% | Muito Alto |

### Risco Fechamento (por SIR)
| Faixa de SIR | Classificação |
|---|---|
| 0 ou N/A | Inexistente |
| > 0 e < 2 | Muito Baixo |
| ≥ 2 e < 4 | Baixo |
| ≥ 4 e ≤ 5 | Alto |
| > 5 | Muito Alto |

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
