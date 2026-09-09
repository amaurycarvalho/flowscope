# RFC-006 — FII Fundamental Metrics Extraction and Deterministic Analysis

**Status:** Proposed
**Version:** 1.0
**Scope:** FIIs de tijolo e híbridos com predominância imobiliária
**Excluded:** FIIs de papel, CRIs/CRAs e fundos cuja geração de resultado não seja predominantemente imobiliária
**Style:** PROBE — Deterministic, Evidence-Based Specification

---

# 1. P — Purpose

Esta RFC especifica um processo determinístico para obter, para qualquer FII elegível, os seguintes indicadores:

- FFO Yield
- Dividend Yield
- P/FFO
- P/VP
- FFO dos últimos 12 meses
- FFO dos últimos 3 meses
- tendência recente do FFO
- classificação textual da tendência
- numero atual de cotistas
- classificação por numero de cotistas
- tamanho patrimonial do fundo
- classificação por tamanho patrimonial
- data de referência dos dados

O processo deve produzir uma tabela equivalente à seguinte:

| Ticker | FFO Yield | Dividend Yield |  P/FFO | P/VP | Tendência FFO |
| ------ | --------: | -------------: | -----: | ---: | ------------- |
| KNRI11 |     7,33% |           6,8% | 13,64x | 0,96 | ↘ Leve queda  |
| HSML11 |     8,28% |           8,5% | 12,08x | 0,78 | ↗ Forte alta  |
| ...    |       ... |            ... |    ... |  ... | ...           |

O objetivo principal não é apenas obter os números, mas garantir que:

1. o resultado seja **reproduzível**;
2. a origem de cada número seja conhecida;
3. a data de referência seja explícita;
4. a fórmula utilizada seja determinística;
5. diferentes execuções com os mesmos inputs produzam o mesmo output;
6. resultados extraordinários não sejam silenciosamente tratados como recorrentes;
7. a tendência do FFO seja determinada por regra objetiva, e não por interpretação subjetiva.

---

# 2. R — Requirements

## R1 — Entrada

O programa SHALL aceitar:

```text
ticker
reference_date
```

Exemplo:

```text
KNRI11
2026-09-08
```

Quando `reference_date` não for informada, SHALL ser utilizada a data do último pregão disponível.

---

## R2 — Universo elegível

O programa SHALL aceitar somente FIIs classificados como:

- tijolo;
- híbridos com predominância imobiliária.

O programa SHALL rejeitar automaticamente:

- FIIs de papel;
- fundos predominantemente CRI/CRA;
- FIAGRO;
- ETFs;
- FIPs;
- fundos de fundos cujo resultado seja predominantemente financeiro;
- ativos que não possam ser classificados de maneira determinística.

A classificação SHALL ser baseada em dados estruturados da fonte primária ou em uma taxonomia previamente versionada.

Não SHALL existir classificação manual durante a execução.

---

## R3 — Fonte primária

A fonte primária para dados regulatórios SHALL ser a CVM.

A CVM disponibiliza:

- Informe Mensal Estruturado;
- Informe Trimestral Estruturado;
- Informe Anual Estruturado;
- Demonstrações Financeiras.

Os Informes Mensais estão disponíveis em arquivos estruturados e possuem histórico desde 2016, com atualização semanal e tratamento de reapresentações.

Os Informes Trimestrais também estão disponibilizados em formato estruturado.

A fonte regulatória SHALL ser preferida para:

- patrimônio líquido;
- número de cotas;
- informações patrimoniais;
- informações financeiras;
- identificação do fundo;
- datas dos informes.

---

## R4 — Fonte de mercado

O preço da cota SHALL ser obtido de uma fonte de mercado determinística.

O programa SHALL armazenar:

```text
ticker
price
price_date
source
```

O preço SHALL corresponder ao:

> último preço de fechamento disponível até `reference_date`.

Não SHALL ser utilizado:

- preço intraday;
- preço médio;
- preço de abertura;
- preço ajustado por dividendos;

para o cálculo do P/VP ou P/FFO.

---

## R5 — Data de corte

Todos os indicadores SHALL respeitar uma única:

```text
reference_date
```

Nenhum dado publicado após essa data SHALL ser utilizado.

Por exemplo:

```text
reference_date = 2026-09-08
```

Um relatório publicado em:

```text
2026-09-10
```

é inelegível, mesmo que contenha dados referentes a agosto.

---

# 3. O — Observability / Evidence

Cada resultado SHALL possuir evidências suficientes para permitir auditoria.

O modelo interno deverá preservar, no mínimo:

```text
MetricEvidence:
    metric
    value
    ticker
    reference_date
    source
    source_date
    formula
    input_values
```

Exemplo:

```text
metric = FFO_YIELD

ticker = HGBS11

value = 0.0816

reference_date = 2026-09-04

source = FUNDAMENTUS

formula = FFO_12M / MARKET_VALUE

input_values:
    FFO_12M = 220777000
    MARKET_VALUE = 2705230000
```

Isso permite responder:

> "Por que o programa calculou 8,16%?"

sem depender de interpretação humana.

---

# 4. B — Behavioral Specification

## B1 — Market Value

O valor de mercado SHALL ser calculado como:

$$
MarketValue =
Price \times SharesOutstanding
$$

Quando a fonte fornecer diretamente o valor de mercado, o programa poderá utilizá-lo somente se:

```text
Price × SharesOutstanding == MarketValue
```

dentro de uma tolerância numérica definida.

Para evitar divergências, a implementação deverá preferencialmente calcular o valor de mercado a partir dos componentes primários.

---

# 5. FFO

## B2 — FFO dos últimos 12 meses

O programa SHALL determinar:

```text
FFO_12M
```

utilizando os resultados disponíveis até `reference_date`.

Quando a fonte fornecer diretamente o FFO acumulado em 12 meses, esse valor SHALL ser utilizado.

Exemplo de estrutura encontrada em bases fundamentalistas:

```text
Últimos 12 meses
FFO = R$ 220.777.000
```

O Fundamentus, por exemplo, apresenta explicitamente FFO nos últimos 12 meses e nos últimos 3 meses.

---

## B3 — FFO dos últimos 3 meses

O programa SHALL obter:

```text
FFO_3M
```

correspondente aos três meses mais recentes disponíveis.

Não SHALL ser assumido que:

```text
FFO_3M = FFO_12M / 4
```

O valor real SHALL ser utilizado sempre que disponível.

---

# 6. FFO Yield

## B4 — Definição

O FFO Yield SHALL ser calculado como:

$$
FFOYield =
\frac{FFO_{12M}}
{MarketValue}
$$

ou, equivalentemente:

$$
FFOYield =
\frac{FFO_{12M}/SharesOutstanding}
{Price}
$$

Multiplicado por 100:

$$
FFOYield_{\%} =
100 \times
\frac{FFO_{12M}}
{MarketValue}
$$

---

## B5 — Exemplo

Se:

```text
FFO_12M = R$ 220.777.000
MarketValue = R$ 2.705.230.000
```

então:

$$
FFOYield =
\frac{220.777.000}{2.705.230.000}
$$

$$
FFOYield = 8,16\%
$$

O resultado coincide com o indicador publicado para HGBS11 na fonte de referência.

---

# 7. P/FFO

## B6 — Definição

O P/FFO SHALL ser calculado por:

$$
P/FFO =
\frac{MarketValue}{FFO_{12M}}
$$

Equivalentemente:

$$
P/FFO =
\frac{Price}
{FFO_{12M}/SharesOutstanding}
$$

---

## B7 — Relação com FFO Yield

Os dois indicadores deverão obedecer:

$$
P/FFO =
\frac{1}{FFOYield}
$$

quando `FFOYield` estiver representado em valor decimal.

Exemplo:

```text
FFO Yield = 8,16%
```

então:

$$
P/FFO =
\frac{1}{0,0816}
=
12,25
$$

---

## B8 — Regra de consistência

O programa SHALL verificar:

```text
abs(P_FFO - (1 / FFO_YIELD)) <= tolerance
```

Se a condição falhar:

```text
DATA_INCONSISTENCY
```

deverá ser gerado.

---

# 8. Dividend Yield

## B9 — Definição

O Dividend Yield SHALL representar os rendimentos distribuídos nos últimos 12 meses em relação ao preço da cota.

$$
DividendYield =
\frac{Dividends_{12M}/SharesOutstanding}
{Price}
$$

ou:

$$
DividendYield =
\frac{Dividends_{12M}}
{MarketValue}
$$

---

## B10 — Rendimentos

O programa SHALL utilizar os rendimentos efetivamente distribuídos.

Não SHALL utilizar:

- dividendo anunciado mas ainda não pago;
- projeção de dividendos;
- último dividendo anualizado;
- média mensal multiplicada por 12.

O período SHALL ser explicitamente determinado:

```text
[reference_date - 12 months, reference_date]
```

considerando as datas de pagamento definidas pela política da fonte.

---

# 9. P/VP

## B11 — Definição

O P/VP SHALL ser:

$$
P/VP =
\frac{MarketValue}{NetAssetValue}
$$

onde:

```text
NetAssetValue = Patrimônio Líquido
```

Equivalentemente:

$$
P/VP =
\frac{Price}
{NAVPerShare}
$$

---

## B12 — Exemplo

Se:

```text
MarketValue = R$ 2,705 bilhões
PL = R$ 2,942 bilhões
```

então:

$$
P/VP =
\frac{2,705}{2,942}
\approx 0,92
$$

que corresponde ao valor apresentado para HGBS11.

---

# 10. FFO Trend

## B13 — Objetivo

A tendência do FFO SHALL medir se a geração operacional recente está:

- acelerando;
- estável;
- desacelerando.

A classificação SHALL ser matemática.

Não SHALL ser baseada em julgamento humano.

---

# 11. Método determinístico da tendência

A métrica base será:

$$
FFO_{3M\ Annualized} =
FFO_{3M} \times 4
$$

Depois:

$$
TrendRatio =
\frac{FFO_{3M}\times4}
{FFO_{12M}}
$$

E:

$$
TrendChange =
TrendRatio - 1
$$

---

# 12. Classificação

A classificação SHALL utilizar os seguintes thresholds:

|     `TrendChange` | Classificação  |
| ----------------: | -------------- |
|         `>= +20%` | ↗ Forte alta   |
|   `+5% a +19,99%` | ↗ Alta         |
| `-4,99% a +4,99%` | → Estável      |
|   `-19,99% a -5%` | ↘ Queda        |
|          `< -20%` | 🔴 Forte queda |

Esses limites SHALL ser constantes de configuração e não poderão ser alterados silenciosamente.

Exemplo:

```yaml
ffo_trend:
  strong_growth: 0.20
  growth: 0.05
  stable: 0.05
  decline: -0.05
  strong_decline: -0.20
```

---

# 13. Exemplo

Suponha:

```text
FFO_12M = 220,777,000
FFO_3M  = 63,802,000
```

Então:

$$
FFO_{3MAnnualized}
=
63,802,000 \times 4
$$

$$
=255,208,000
$$

e:

$$
TrendChange =
\frac{255,208,000}{220,777,000}-1
$$

$$
=15,59\%
$$

Logo:

```text
↗ Alta
```

---

# 14. Importante: tendência não significa crescimento anual

O indicador acima SHALL ser denominado:

```text
FFO Recent Momentum
```

e não:

```text
FFO Growth YoY
```

porque ele compara o ritmo dos três meses mais recentes com o ritmo médio dos últimos 12 meses.

Ele responde:

> "O FFO recente está acima ou abaixo do ritmo que prevaleceu nos últimos 12 meses?"

Ele não responde:

> "O FFO cresceu X% em relação ao mesmo período do ano anterior?"

Essa distinção SHALL permanecer explícita na implementação.

---

# 15. Dividend / FFO Coverage

Embora não faça parte da tabela principal, o programa SHALL calcular internamente:

$$
FFOPayout =
\frac{Dividends_{12M}}
{FFO_{12M}}
$$

Esse indicador é necessário para identificar situações como:

```text
Dividend Yield >> FFO Yield
```

que podem exigir investigação.

Exemplo:

```text
FFO Yield = 5,66%
Dividend Yield = 12,8%
```

não SHALL ser classificado automaticamente como "bom" ou "ruim".

Deverá ser classificado como:

```text
DISTRIBUTION_REQUIRES_REVIEW
```

---

# Classificação por numero de cotistas

| Classe            | Número de cotistas | Relação com a mediana | Interpretação                      |
| ----------------- | -----------------: | --------------------- | ---------------------------------- |
| **Micro**         |              1–250 | < 0,11 × mediana      | Base de investidores muito pequena |
| **Muito Pequeno** |          251–1.000 | 0,11–0,44 × mediana   | Fundo abaixo da escala típica      |
| **Pequeno**       |        1.001–5.000 | 0,44–2,18 × mediana   | Fundo abaixo da escala típica      |
| **Médio**         |       5.001–35.000 | 2,18–10,9 × mediana   | **Faixa central do mercado**       |
| **Grande**        |      35.001–65.000 | 10,9–43,7 × mediana   | Base de investidores relevante     |
| **Muito grande**  |     65.001–100.000 | 10,9–43,7 × mediana   | Ampla distribuição                 |
| **Gigante**       |           >100.000 | >43,7 × mediana       | Distribuição excepcional           |

# Classificação por tamanho patrimonial

| Classe           |      Patrimônio líquido | Interpretação                  |
| ---------------- | ----------------------: | ------------------------------ |
| **Micro**        |         < R$ 50 milhões | Estrutura patrimonial pequena  |
| **Pequeno**      |       R$ 50–100 milhões | Fundo abaixo da escala típica  |
| **Médio**        |      R$ 100–250 milhões | **Faixa central**              |
| **Grande**       |      R$ 250–500 milhões | Fundo de porte relevante       |
| **Muito grande** | R$ 500 milhões–1 bilhão | Grande escala patrimonial      |
| **Gigante**      |           > R$ 1 bilhão | Escala patrimonial excepcional |

---

# 16. Extraordinary Result Detection

O sistema SHALL identificar quando a diferença entre distribuição e FFO for material.

Regra inicial:

```text
if DividendYield > FFOYield * 1.25:
    flag = "HIGH_DISTRIBUTION_VS_FFO"
```

Essa regra não altera os indicadores.

Ela apenas cria uma evidência adicional.

---

# 17. Data Freshness

Cada indicador deverá possuir:

```text
market_data_date
financial_data_date
report_date
```

O programa SHALL impedir silenciosamente a mistura de dados incompatíveis.

Exemplo permitido:

```text
Preço: 08/09/2026
FFO: período encerrado em 30/06/2026
PL: 30/06/2026
```

desde que esse seja o conjunto de dados mais recente publicado até 08/09/2026.

---

# 18. Reapresentações

A CVM disponibiliza atualizações e reapresentações dos Informes Mensais.

Quando existirem múltiplas versões para o mesmo:

```text
ticker + reference_period
```

o programa SHALL selecionar:

```text
latest_valid_submission <= reference_date
```

A versão anterior SHALL permanecer registrada para auditoria.

---

# 19. Deterministic Source Resolution

A resolução das fontes SHALL seguir esta prioridade:

### Nível 1 — Regulatório

```text
CVM
```

para:

- PL;
- cotas;
- dados financeiros;
- informes.

### Nível 2 — Mercado

Fonte de cotação para:

- fechamento;
- histórico de preços.

### Nível 3 — Derivação

Indicadores calculados:

- Market Value;
- FFO Yield;
- P/FFO;
- P/VP;
- Dividend Yield;
- FFO Momentum.

### Nível 4 — Validação

Fontes secundárias poderão ser utilizadas somente para:

```text
cross-check
```

e não deverão substituir silenciosamente os dados primários.

---

# 20. Normalização

Todos os valores monetários SHALL ser normalizados para:

```text
BRL
```

e armazenados internamente como números decimais de precisão adequada.

Percentuais SHALL ser armazenados como:

```text
0.0816
```

e apresentados como:

```text
8,16%
```

Ratios SHALL ser armazenados como:

```text
12.25
```

e apresentados como:

```text
12,25x
```

---

# 21. Rounding

O cálculo interno SHALL utilizar a precisão completa.

O arredondamento SHALL ocorrer somente na apresentação.

Formato:

```text
FFO Yield       → 2 casas decimais
Dividend Yield  → 1 casa decimal
P/FFO           → 2 casas decimais
P/VP            → 2 casas decimais
```

Exemplo:

```text
0.08163472
```

deverá ser apresentado como:

```text
8,16%
```

---

# 22. Missing Data

Quando uma variável obrigatória não estiver disponível, o programa SHALL retornar:

```text
N/A
```

e SHALL NOT:

- estimar;
- extrapolar;
- substituir por dado antigo sem marcar;
- utilizar outra fonte sem registrar o fallback.

---

# 23. Zero and Negative Values

Se:

```text
FFO_12M <= 0
```

então:

```text
FFO Yield = N/A
P/FFO = N/A
```

porque não existe interpretação econômica convencional de P/FFO positivo nesse caso.

Se:

```text
MarketValue <= 0
```

o registro SHALL ser inválido.

Se:

```text
PL <= 0
```

então:

```text
P/VP = N/A
```

---

# 24. Output Contract

O resultado final SHALL possuir o seguinte schema:

```text
FIIAnalysis:
    ticker
    reference_date

    price
    price_date

    shares_outstanding
    market_value

    net_asset_value
    nav_per_share

    ffo_12m
    ffo_3m
    ffo_yield
    p_ffo

    dividends_12m
    dividend_yield

    p_vp

    ffo_recent_annualized
    ffo_trend_change
    ffo_trend_class

    ffo_payout

    data_quality
    warnings
```

---

# 25. Output Table

A tabela pública SHALL conter:

| Campo          | Formato               |
| -------------- | --------------------- |
| Ticker         | `XXXX11`              |
| FFO Yield      | `0.00%`               |
| Dividend Yield | `0.0%`                |
| P/FFO          | `0.00x`               |
| P/VP           | `0.00x`               |
| Tendência FFO  | classificação textual |

Campos auxiliares poderão ser disponibilizados em modo detalhado.

---

# 26. Deterministic Pipeline

O processamento completo SHALL seguir:

```text
INPUT
  │
  ▼
Normalize Ticker
  │
  ▼
Validate FII Eligibility
  │
  ▼
Resolve Reference Date
  │
  ▼
Load CVM Data
  │
  ├── Monthly Reports
  ├── Quarterly Reports
  └── Financial Statements
  │
  ▼
Resolve Latest Valid Data
  │
  ▼
Load Market Price
  │
  ▼
Build Financial Snapshot
  │
  ├── Shares
  ├── Price
  ├── Market Value
  ├── NAV
  ├── FFO 12M
  ├── FFO 3M
  └── Dividends 12M
  │
  ▼
Calculate Metrics
  │
  ├── FFO Yield
  ├── P/FFO
  ├── Dividend Yield
  ├── P/VP
  └── FFO Trend
  │
  ▼
Run Consistency Checks
  │
  ▼
Generate Evidence
  │
  ▼
Format Output
```

---

# 27. Reference Implementation

A implementação SHALL separar:

```text
domain/
    models.py
    metrics.py
    classification.py
    trend.py

application/
    analyze_fii.py
    build_comparison.py

infrastructure/
    cvm/
    market_data/
    cache/

presentation/
    table.py
```

O domínio não deverá conhecer:

- CVM;
- HTTP;
- HTML;
- CSV;
- APIs;
- scraping.

---

# 28. Domain Model

O domínio deverá trabalhar sobre um snapshot normalizado:

```python
@dataclass(frozen=True)
class FiiSnapshot:
    ticker: str
    reference_date: date
    price: Decimal
    shares: Decimal
    nav: Decimal
    ffo_12m: Decimal
    ffo_3m: Decimal
    dividends_12m: Decimal
```

Os cálculos serão funções puras:

```python
def market_value(snapshot):
    return snapshot.price * snapshot.shares
```

```python
def ffo_yield(snapshot):
    return snapshot.ffo_12m / market_value(snapshot)
```

```python
def p_ffo(snapshot):
    return market_value(snapshot) / snapshot.ffo_12m
```

```python
def p_vp(snapshot):
    return market_value(snapshot) / snapshot.nav
```

```python
def dividend_yield(snapshot):
    return snapshot.dividends_12m / market_value(snapshot)
```

```python
def ffo_trend(snapshot):
    annualized = snapshot.ffo_3m * 4
    return annualized / snapshot.ffo_12m - 1
```

---

# 29. Property-Based Invariants

A implementação SHALL testar invariantes matemáticos.

### INV-001

```text
P/FFO × FFO Yield = 1
```

### INV-002

```text
MarketValue / Shares = Price
```

### INV-003

```text
MarketValue / NAV = P/VP
```

### INV-004

```text
FFO Yield >= 0
```

somente quando:

```text
FFO_12M > 0
```

### INV-005

A alteração da formatação não poderá alterar o valor interno.

---

# 30. Golden Test

O projeto SHALL possuir datasets congelados.

Exemplo:

```json
{
  "ticker": "HGBS11",
  "reference_date": "2026-09-04",
  "price": 18.74,
  "shares": 144355726,
  "nav": 2942000000,
  "ffo_12m": 220777000,
  "ffo_3m": 63802000,
  "dividends_12m": 213080000
}
```

Resultado esperado:

```json
{
  "ffo_yield": 0.0816,
  "p_ffo": 12.25,
  "p_vp": 0.92,
  "dividend_yield": 0.084,
  "ffo_trend": "UP"
}
```

O teste SHALL permanecer congelado mesmo quando os dados externos forem atualizados.

---

# 31. Deterministic Comparison

Para uma lista:

```text
KNRI11
HSML11
XPML11
RBVA11
TVRI11
BTLG11
HGBS11
VISC11
NSLU11
HCRI11
TRXF11
HGLG11
```

o programa SHALL:

1. normalizar os tickers;
2. ordenar alfabeticamente para processamento;
3. analisar cada FII independentemente;
4. gerar um objeto de resultado por ticker;
5. ordenar o output segundo a ordem de entrada ou uma ordenação configurável;
6. nunca permitir que o resultado de um FII influencie o cálculo de outro.

---

# 32. Quality Classification

Cada registro deverá receber:

```text
data_quality =
    COMPLETE
    PARTIAL
    WARNING
    INVALID
```

### COMPLETE

Todos os dados obrigatórios estão disponíveis.

### PARTIAL

Um dado não essencial está ausente.

### WARNING

Os indicadores podem ser calculados, mas existe uma anomalia.

Exemplos:

```text
Dividend Yield > FFO Yield
FFO_3M < 0
FFO trend strongly negative
```

### INVALID

Dados necessários ao cálculo estão ausentes ou inconsistentes.

---

# 33. Example — HGBS11

Dados:

```text
Preço                    = R$ 18,74
Cotas                    = 144.355.726
Patrimônio Líquido       = R$ 2.942.000.000
FFO 12M                  = R$ 220.777.000
FFO 3M                   = R$ 63.802.000
Rendimentos 12M         = R$ 213.080.000
```

Market Value:

$$
18,74 \times 144.355.726
\approx
R\$2,705\ bilhões
$$

FFO Yield:

$$
220,777 / 2.705,23
=
8,16\%
$$

P/FFO:

$$
2.705,23 / 220,777
=
12,25x
$$

P/VP:

$$
2.705,23 / 2.942
=
0,92x
$$

FFO Momentum:

$$
(63,802\times4)/220,777-1
\approx15,6\%
$$

Resultado:

```text
HGBS11
FFO Yield:       8,16%
Dividend Yield:  8,4%
P/FFO:          12,25x
P/VP:            0,92x
FFO Trend:       ↗ Alta
```

Os dados-base publicados pelo Fundamentus para HGBS11 apresentam FFO de R$ 220,777 milhões nos últimos 12 meses, R$ 63,802 milhões nos últimos três meses, FFO Yield de 8,16%, Dividend Yield de 8,4% e P/VP de 0,92.

---

# 34. Reference Architecture

A arquitetura recomendada é:

```text
                    ┌─────────────────┐
                    │     CLI/API     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ AnalyzeFii      │
                    │ Use Case        │
                    └────────┬────────┘
                             │
             ┌───────────────┼────────────────┐
             │               │                │
             ▼               ▼                ▼
       ┌──────────┐   ┌─────────────┐  ┌─────────────┐
       │ CVM      │   │ Market Data │  │ FII         │
       │ Gateway  │   │ Gateway     │  │ Classifier  │
       └────┬─────┘   └──────┬──────┘  └─────────────┘
            │                │
            └────────┬───────┘
                     ▼
             ┌───────────────┐
             │ Normalized    │
             │ Snapshot      │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │ Metric Engine │
             └───────┬───────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       FFO Yield   P/FFO      P/VP
          │          │          │
          └──────────┼──────────┘
                     ▼
             ┌───────────────┐
             │ Trend Engine  │
             └───────┬───────┘
                     ▼
             ┌───────────────┐
             │ Evidence &    │
             │ Quality       │
             └───────┬───────┘
                     ▼
             ┌───────────────┐
             │ Final Table   │
             └───────────────┘
```

---

# 35. Non-Goals

Esta RFC NÃO especifica:

- recomendação de compra;
- valuation absoluto;
- preço-alvo;
- previsão de dividendos;
- previsão de FFO;
- análise qualitativa de imóveis;
- análise de gestores;
- análise de contratos;
- análise de risco de crédito;
- análise de FIIs de papel.

O sistema produz **métricas e evidências**, não uma decisão de investimento.

---

# 36. Key Design Principle

A regra fundamental desta RFC é:

> **O programa SHALL calcular; o programa SHALL NOT interpretar silenciosamente.**

Por exemplo:

```text
FFO Yield = 17%
```

é um fato calculado.

Já:

```text
"FII barato"
```

é uma interpretação.

A primeira pertence a esta RFC.

A segunda pertence a uma camada posterior de análise.

Da mesma forma:

```text
Dividend Yield > FFO Yield
```

é uma evidência.

Enquanto:

```text
"dividendos insustentáveis"
```

é uma conclusão que exige análise adicional.

---

# 37. Acceptance Criteria

A implementação será considerada conforme quando:

- [ ] aceitar qualquer ticker elegível;
- [ ] rejeitar FIIs de papel;
- [ ] respeitar uma `reference_date`;
- [ ] utilizar somente informações disponíveis até a data de corte;
- [ ] identificar a versão válida mais recente dos informes;
- [ ] calcular Market Value deterministicamente;
- [ ] calcular FFO Yield;
- [ ] calcular Dividend Yield;
- [ ] calcular P/FFO;
- [ ] calcular P/VP;
- [ ] calcular FFO Momentum;
- [ ] classificar a tendência segundo thresholds fixos;
- [ ] gerar evidências dos cálculos;
- [ ] detectar inconsistências;
- [ ] produzir o mesmo resultado para o mesmo conjunto de inputs;
- [ ] possuir testes golden;
- [ ] possuir testes das invariantes matemáticas;
- [ ] não depender de interpretação humana durante o cálculo.

---

# 38. Future Extensions

A arquitetura deverá permitir posteriormente adicionar:

```text
FFO Growth YoY
Dividend Payout
Vacancy
LTV
Cap Rate
Revenue Growth
NAV Growth
Dividend Stability
FFO Stability
```

sem alterar o pipeline básico de aquisição e normalização.

Uma futura camada de scoring poderá transformar os indicadores em:

```text
Value Score
Income Score
Growth Score
Quality Score
Risk Score
```

mas essa camada deverá permanecer separada do motor determinístico de métricas.

---

# 39. Summary

O sistema especificado nesta RFC transforma:

```text
FII ticker
      +
reference date
```

em:

```text
              ┌─────────────────┐
              │ FII Snapshot    │
              └────────┬────────┘
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   FFO Yield        Dividend          P/VP
       │              Yield             │
       ▼               ▼                ▼
    P/FFO          Distribution       NAV
                       │
                       ▼
                  FFO Momentum
                       │
                       ▼
                 Evidence Layer
                       │
                       ▼
                  Final Table
```

A característica central é a **reprodutibilidade**:

> **mesmo ticker + mesma data de referência + mesmos dados de entrada + mesma versão da RFC = mesmo resultado.**

Isso permite que a tabela deixe de ser uma coleta manual de indicadores e passe a ser o produto de um **pipeline quantitativo auditável e determinístico**.

# 40. Technical Reference

Leia a `RFC-007` para informações mais técnicas que apoiam a implementação da RFC corrente.

Em resumo, a RFC-007 contém o **FII Fundamental Data Pipeline**: technical implementation specification defining data-source adapters, temporal resolution, normalization, FFO/dividend acquisition, deterministic metric calculation, evidence lineage, caching, validation and test contracts for the FII fundamental-analysis pipeline.
