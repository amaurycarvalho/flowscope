# fii-fundamental-metrics Specification

## Purpose
Calcular deterministicamente as métricas fundamentalistas de FIIs elegíveis (tijolo/híbrido) — FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum, número de cotistas e patrimônio — com evidência por métrica, conforme as RFC-006/007.

## Requirements

### Requirement: Valor de mercado
O sistema DEVE calcular o valor de mercado como `price × shares_outstanding`, usando `decimal.Decimal` e precisão completa, sem arredondamento intermediário.

#### Scenario: Cálculo do valor de mercado
- **WHEN** price é `18,74` e shares_outstanding é `144355726`
- **THEN** o valor de mercado DEVE ser `18,74 × 144355726`

### Requirement: FFO Yield
O sistema DEVE calcular o FFO Yield como `FFO_12M / MarketValue`, armazenando o valor em decimal e apresentando como percentual com 2 casas decimais.

#### Scenario: FFO Yield calculado
- **WHEN** FFO_12M é `220777000` e MarketValue é `2705230000`
- **THEN** o FFO Yield DEVE ser aproximadamente `0,0816` (8,16%)

#### Scenario: FFO negativo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o FFO Yield DEVE ser `N/A`

### Requirement: P/FFO
O sistema DEVE calcular o P/FFO como `MarketValue / FFO_12M`.

#### Scenario: P/FFO calculado
- **WHEN** MarketValue é `2705230000` e FFO_12M é `220777000`
- **THEN** o P/FFO DEVE ser aproximadamente `12,25`

#### Scenario: P/FFO com FFO não positivo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o P/FFO DEVE ser `N/A`

### Requirement: P/VP
O sistema DEVE calcular o P/VP como `MarketValue / NetAssetValue`, onde NetAssetValue é o patrimônio líquido.

#### Scenario: P/VP calculado
- **WHEN** MarketValue é `2705230000` e NetAssetValue é `2942000000`
- **THEN** o P/VP DEVE ser aproximadamente `0,92`

#### Scenario: Patrimônio líquido não positivo
- **WHEN** NetAssetValue é menor ou igual a zero
- **THEN** o P/VP DEVE ser `N/A`

### Requirement: P/L

O sistema DEVE expor, por ticker, a razão `P/L` como a quantidade de anos para recuperar o investimento. Para ativos do tipo `Papel`, DEVE usar o valor reportado pela fonte. Para FII, DEVE calcular `P/L = Preço / (Último dividendo × 12)`, anualizando o dividendo mensal, por função pura e determinística. O sistema DEVE exibir `N/A` quando o valor não estiver disponível ou o último dividendo for ausente ou zero.

#### Scenario: P/L de ação reportado pela fonte
- **WHEN** a fonte reporta `P/L` para um ativo do tipo `Papel`
- **THEN** o `P/L` DEVE ser o valor reportado

#### Scenario: P/L de FII calculado
- **WHEN** um FII possui preço `18,74` e último dividendo mensal `0,55`
- **THEN** o `P/L` DEVE ser aproximadamente `2,84`

#### Scenario: P/L indisponível
- **WHEN** o último dividendo de um FII é ausente ou zero, ou a fonte não reporta `P/L` para o Papel
- **THEN** o `P/L` DEVE ser `N/A`

### Requirement: Dividend Yield (12 meses)
O sistema DEVE calcular o Dividend Yield como `Dividends_12M / MarketValue`, usando rendimentos efetivamente distribuídos nos últimos 12 meses.

#### Scenario: Dividend Yield calculado
- **WHEN** Dividends_12M é `213080000` e MarketValue é `2705230000`
- **THEN** o Dividend Yield DEVE ser aproximadamente `0,084` (8,4%)

### Requirement: Consistência entre P/FFO e FFO Yield
O sistema DEVE verificar que `P/FFO × FFO Yield ≈ 1` dentro de uma tolerância configurada; em caso de violação, DEVE gerar uma indicação de `DATA_INCONSISTENCY`.

#### Scenario: Consistência mantida
- **WHEN** P/FFO é `12,25` e FFO Yield é `0,0816`
- **THEN** o produto DEVE estar dentro da tolerância de 1

### Requirement: FFO Momentum
O sistema DEVE calcular o FFO Momentum como `(FFO_3M × 4) / FFO_12M − 1`.

#### Scenario: FFO Momentum calculado
- **WHEN** FFO_3M é `63802000` e FFO_12M é `220777000`
- **THEN** o FFO Momentum DEVE ser aproximadamente `0,156` (+15,6%)

#### Scenario: FFO Momentum com FFO não positivo
- **WHEN** FFO_12M é menor ou igual a zero
- **THEN** o FFO Momentum DEVE ser `N/A`

### Requirement: Classificação da tendência do FFO
O sistema DEVE classificar o FFO Momentum em faixas determinísticas e configuráveis: `FORTE_ALTA` (≥ +20%), `ALTA` (≥ +5%), `ESTAVEL` (> −5%), `QUEDA` (≥ −20%) e `FORTE_QUEDA` (< −20%).

#### Scenario: Tendência alta
- **WHEN** o FFO Momentum é `0,156`
- **THEN** a classificação DEVE ser `ALTA`

#### Scenario: Tendência em forte queda
- **WHEN** o FFO Momentum é menor que `−0,20`
- **THEN** a classificação DEVE ser `FORTE_QUEDA`

### Requirement: Classificação por número de cotistas
O sistema DEVE expor, por ticker, o número atual de cotistas e sua classificação determinística (`MICRO`, `MUITO_PEQUENO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares absolutos fixos da RFC-006, exibindo `N/A` quando o número não estiver disponível. Para ativos do tipo `Papel`, o número de cotistas corresponde à quantidade de acionistas obtida da CVM, reutilizando a mesma classificação determinística.

#### Scenario: Cotistas em faixa média
- **WHEN** o número de cotistas está entre 5.001 e 35.000
- **THEN** a classificação DEVE ser `MEDIO` e o número de cotistas DEVE ser exposto

#### Scenario: Cotistas indisponíveis
- **WHEN** o número de cotistas não está disponível na fonte
- **THEN** o número e a classificação DEVEM ser `N/A`

#### Scenario: Acionistas de ação classificados
- **WHEN** um ativo do tipo `Papel` possui quantidade de acionistas obtida da CVM
- **THEN** o número de cotistas DEVE ser essa quantidade e a classificação DEVE usar os mesmos limiares determinísticos

### Requirement: Classificação por tamanho patrimonial
O sistema DEVE expor, por ticker, o tamanho patrimonial do fundo (patrimônio líquido) e sua classificação determinística (`MICRO`, `PEQUENO`, `MEDIO`, `GRANDE`, `MUITO_GRANDE`, `GIGANTE`) conforme os limiares absolutos fixos da RFC-006, exibindo `N/A` quando o valor não estiver disponível.

#### Scenario: Patrimônio em faixa grande
- **WHEN** o patrimônio líquido está entre R$ 250 milhões e R$ 500 milhões
- **THEN** a classificação DEVE ser `GRANDE` e o valor DEVE ser exposto

#### Scenario: Patrimônio indisponível
- **WHEN** o patrimônio líquido não está disponível na fonte
- **THEN** o valor e a classificação DEVEM ser `N/A`

### Requirement: Evidência por métrica
O sistema DEVE produzir, para cada métrica calculada, uma evidência contendo métrica, valor, fórmula, valores de entrada, fontes, data de referência e versão de cálculo.

#### Scenario: Evidência do FFO Yield
- **WHEN** o FFO Yield é calculado
- **THEN** DEVE existir evidência registrando a fórmula `ffo_12m / market_value`, os valores de entrada e as fontes utilizadas

### Requirement: Não elegível gera N/A
O sistema DEVE preencher cada métrica (FFO Yield, Dividend Yield, P/FFO, P/VP, FFO Momentum) sempre que a fonte fornecer os dados, independentemente do tipo ou sub-tipo do ticker, exibindo `N/A` somente quando o dado não existir.

#### Scenario: Métricas disponíveis na fonte
- **WHEN** a fonte fornece os dados de FFO, dividendo e patrimônio para o ticker
- **THEN** FFO Yield, Dividend Yield, P/FFO, P/VP e FFO Momentum DEVEM ser preenchidos

#### Scenario: Ação gera N/A nas métricas FFO
- **WHEN** um ativo do tipo `Papel` é analisado e a fonte não fornece FFO
- **THEN** somente as métricas dependentes de FFO DEVEM ser `N/A`

#### Scenario: Dado ausente na fonte
- **WHEN** a fonte não fornece o dado de uma métrica
- **THEN** somente aquela métrica DEVE ser `N/A`

### Requirement: Data de referência dos dados
O sistema DEVE expor, por ticker, a data de referência dos dados de mercado, usando `Data últ cot` do Fundamentus quando disponível e, na sua ausência, a data do último fechamento da B3 utilizado no cálculo, exibindo `N/A` quando nenhuma das fontes fornecer uma data.

#### Scenario: Data de referência disponível
- **WHEN** o Fundamentus informa `Data últ cot`
- **THEN** a data de referência DEVE ser essa data

#### Scenario: Fundamentus indisponível com preço da B3
- **WHEN** o Fundamentus não informa `Data últ cot` e a análise usa um fechamento da B3
- **THEN** a data de referência DEVE ser a data desse fechamento

#### Scenario: Data de referência indisponível
- **WHEN** não há data de última cotação nem preço de fechamento
- **THEN** a data de referência DEVE ser `N/A`

### Requirement: Preço Típico e P / PT

O sistema DEVE calcular o `Preço Típico` como `(Cotação Max 52 sem + Cotação Min 52 sem + Cotação) / 3` e o `P / PT` como `(Cotação − Preço Típico) / Preço Típico`, por funções puras e determinísticas em `Decimal`, exibindo `N/A` quando qualquer insumo estiver ausente ou o Preço Típico for zero.

#### Scenario: Preço Típico calculado
- **WHEN** a cotação é `10`, a mínima de 52 semanas é `8` e a máxima é `12`
- **THEN** o Preço Típico DEVE ser `10`

#### Scenario: P / PT calculado
- **WHEN** a cotação é `9` e o Preço Típico é `10`
- **THEN** o P / PT DEVE ser `-0,10` (−10%)

#### Scenario: Insumo ausente
- **WHEN** a cotação, a mínima ou a máxima de 52 semanas não está disponível
- **THEN** o Preço Típico e o P / PT DEVEM ser `N/A`

### Requirement: Percentuais por indexador na análise

O sistema DEVE expor, por ticker de FII, os percentuais de patrimônio por indexador fornecidos pela CVM, omitindo os indexadores sem valor.

#### Scenario: Percentuais disponíveis
- **WHEN** a CVM fornece os percentuais de `IPCA`, `IGP-M`, `INPC` e `INCC` para o FII
- **THEN** a análise DEVE expor os percentuais por indexador

#### Scenario: Sem percentuais
- **WHEN** a CVM não fornece percentuais para o ticker
- **THEN** nenhum percentual DEVE ser exposto, sem impedir as demais métricas

### Requirement: Razões FFO/Receita, Dividendos/Receita e Dividendos/FFO

O sistema DEVE calcular, para tickers do tipo `FII`, as razões `FFO/Receita = (FFO ÷ Receita) × 100`, `Dividendos/Receita = (Rend. Distribuído ÷ Receita) × 100` e `Dividendos/FFO = (Rend. Distribuído ÷ FFO) × 100`, nos períodos de 12 meses e 3 meses, a partir dos demonstrativos do Fundamentus, tratando `Rend. Distribuído` como Dividendos. Os valores DEVEM ser armazenados como fração em `Decimal` e apresentados em notação percentual com uma casa decimal. Para tickers do tipo `Papel`, as razões DEVEM ser `N/A`. Insumo ausente DEVE resultar em `N/A` na razão correspondente, sem impedir as demais.

#### Scenario: FFO/Receita calculado
- **WHEN** um FII possui FFO de 12 meses `417655000` e Receita de 12 meses `478420000`
- **THEN** `FFO/Receita (12m)` DEVE ser aproximadamente `87,3%`

#### Scenario: Dividendos/Receita calculado
- **WHEN** um FII possui Rend. Distribuído de 12 meses `553687000` e Receita de 12 meses `478420000`
- **THEN** `Dividendos/Receita (12m)` DEVE ser aproximadamente `115,7%`

#### Scenario: Dividendos/FFO calculado
- **WHEN** um FII possui Rend. Distribuído de 3 meses `112411000` e FFO de 3 meses `125081000`
- **THEN** `Dividendos/FFO (3m)` DEVE ser aproximadamente `89,9%`

#### Scenario: Tipo Papel não calcula as razões
- **WHEN** o ticker é do tipo `Papel`
- **THEN** as seis razões DEVEM ser `N/A`

#### Scenario: Insumo ausente
- **WHEN** a fonte não fornece Receita, FFO ou Rend. Distribuído de um período
- **THEN** somente as razões que dependem desse insumo DEVEM ser `N/A`

### Requirement: Tratamento de insumos negativos nas razões

O sistema DEVE substituir o valor numérico por texto quando um insumo do denominador for negativo: `Receita negativa` quando a Receita for negativa, `FFO negativo` quando o FFO for negativo e `Receita e FFO negativos` quando ambos forem negativos na razão `FFO/Receita`. Divisão por zero DEVE resultar em `N/A`. O texto DEVE ser aplicado apenas no campo da razão correspondente, sem afetar as demais.

#### Scenario: Receita negativa
- **WHEN** a Receita do período é negativa e o FFO é positivo
- **THEN** `FFO/Receita` e `Dividendos/Receita` DEVEM exibir `Receita negativa`

#### Scenario: FFO negativo
- **WHEN** o FFO do período é negativo e a Receita é positiva
- **THEN** `Dividendos/FFO` DEVE exibir `FFO negativo`

#### Scenario: Receita e FFO negativos
- **WHEN** a Receita e o FFO do período são ambos negativos
- **THEN** `FFO/Receita` DEVE exibir `Receita e FFO negativos`

#### Scenario: Divisão por zero
- **WHEN** o denominador da razão é zero
- **THEN** a razão correspondente DEVE exibir `N/A`

### Requirement: Dividend Yield de FII recalculado pelo último dividendo

O sistema DEVE recalcular o Dividend Yield de tickers do tipo `FII` como `(último dividendo × 12) ÷ P (Cotação)` quando o último dividendo e a cotação atual existirem e a cotação for diferente de zero. Quando qualquer um desses insumos não existir, o sistema DEVE manter o Dividend Yield do Fundamentus. Para tickers do tipo `Papel`, o sistema NÃO DEVE recalcular o Dividend Yield, preservando os fallbacks existentes.

#### Scenario: Recálculo com último dividendo
- **WHEN** um FII possui último dividendo `0,10` e cotação `10,00`
- **THEN** o Dividend Yield DEVE ser aproximadamente `0,12` (12,0% ao ano sobre a cotação atual)

#### Scenario: Sem último dividendo ou cotação
- **WHEN** o último dividendo ou a cotação de um FII não está disponível
- **THEN** o Dividend Yield DEVE ser o valor do Fundamentus, quando disponível

#### Scenario: Tipo Papel preserva o fallback
- **WHEN** o ticker é do tipo `Papel`
- **THEN** o Dividend Yield NÃO DEVE ser recalculado pelo último dividendo

### Requirement: Tendência do FFO pela variação da margem FFO/Receita

O sistema DEVE classificar a tendência do FFO de tickers do tipo `FII` pela diferença, em pontos percentuais, entre `FFO/Receita (3m)` e `FFO/Receita (12m)`, reutilizando as cinco faixas determinísticas existentes: `FORTE_ALTA` (≥ +20 p.p.), `ALTA` (≥ +5 p.p.), `ESTAVEL` (> −5 p.p.), `QUEDA` (≥ −20 p.p.) e `FORTE_QUEDA` (< −20 p.p.). Quando uma das margens não estiver disponível (inclusive por insumo negativo ou ausente) ou o ticker for do tipo `Papel`, a tendência DEVE ser `N/A`.

#### Scenario: Margem estável
- **WHEN** `FFO/Receita (12m)` é `87,3%` e `FFO/Receita (3m)` é `85,5%`
- **THEN** a tendência DEVE ser `ESTAVEL` (diferença de −1,8 p.p.)

#### Scenario: Margem em leve queda
- **WHEN** `FFO/Receita (12m)` é `104,0%` e `FFO/Receita (3m)` é `94,5%`
- **THEN** a tendência DEVE ser `QUEDA` (diferença de −9,5 p.p.)

#### Scenario: Margem indisponível
- **WHEN** `FFO/Receita (12m)` ou `FFO/Receita (3m)` é `N/A` ou um texto de insumo negativo
- **THEN** a tendência DEVE ser `N/A`
