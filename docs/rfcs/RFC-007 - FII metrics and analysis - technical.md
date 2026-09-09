# RFC-007 — FII Fundamental Data Pipeline

**Status:** Proposed
**Version:** 1.0
**Type:** Technical Annex
**Parent RFC:** FII Fundamental Metrics Extraction and Deterministic Analysis
**System:** FlowScope
**Scope:** FIIs de tijolo e híbridos predominantemente imobiliários
**Language:** English for identifiers and contracts; Portuguese may be used in user-facing descriptions

---

# 1. Purpose

This RFC defines the operational implementation of the FII fundamental-analysis pipeline specified by the parent RFC.

It SHALL define:

* external data sources;
* source adapters;
* data acquisition;
* raw-data persistence;
* normalization;
* ticker resolution;
* temporal resolution;
* financial snapshot construction;
* FFO acquisition;
* dividend acquisition;
* market-price acquisition;
* metric calculation;
* FFO trend calculation;
* validation;
* evidence generation;
* caching;
* error handling;
* deterministic replay;
* golden tests.

The implementation SHALL be designed so that:

> Given the same normalized input snapshot, reference date and implementation version, FlowScope SHALL produce exactly the same analytical result.

---

# 2. Relationship With Parent RFC

The parent RFC defines the **what** and **why**:

```text
FII
 ├── FFO Yield
 ├── Dividend Yield
 ├── P/FFO
 ├── P/VP
 └── FFO Recent Momentum
```

This RFC defines the **how**:

```text
External Sources
       │
       ▼
Source Adapters
       │
       ▼
Raw Data
       │
       ▼
Normalization
       │
       ▼
FII Snapshot
       │
       ▼
Metric Engine
       │
       ▼
Validation
       │
       ▼
Evidence
       │
       ▼
FlowScope Output
```

In case of conflict, the parent RFC defines the business semantics and this RFC defines the implementation details.

---

# 3. Design Principles

The implementation SHALL follow the following principles.

## 3.1 Source independence

Domain logic SHALL NOT depend directly on:

* CVM;
* Fundamentus;
* StatusInvest;
* APIs;
* HTTP;
* CSV;
* HTML;
* JSON.

External sources SHALL be isolated behind adapters.

---

## 3.2 Determinism

The calculation layer SHALL be pure.

Given:

```text
same snapshot
+
same configuration
+
same calculation version
```

the result SHALL be identical.

---

## 3.3 Evidence first

Every calculated metric SHALL be traceable to:

```text
source data
      ↓
normalized value
      ↓
formula
      ↓
result
```

---

## 3.4 No silent fallback

If a source fails, FlowScope SHALL NOT silently replace it with another source.

Fallbacks SHALL be explicit and recorded in the evidence model.

---

## 3.5 Acquisition ≠ calculation

The system SHALL separate:

```text
Acquisition
Normalization
Calculation
Validation
Presentation
```

---

# 4. High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│                  FlowScope                   │
│                                              │
│  ┌──────────────┐                            │
│  │ Analyze FII  │                            │
│  │ Use Case     │                            │
│  └──────┬───────┘                            │
│         │                                    │
│         ▼                                    │
│  ┌──────────────────────┐                    │
│  │ Fundamental Analysis │                    │
│  │ Service              │                    │
│  └──────────┬───────────┘                    │
│             │                                │
│     ┌───────┼───────────────┐                │
│     ▼       ▼               ▼                │
│ ┌───────┐ ┌────────────┐ ┌───────────────┐  │
│ │ FII   │ │ Financial  │ │ Market Data   │  │
│ │ Repo  │ │ Repository │ │ Repository    │  │
│ └───┬───┘ └─────┬──────┘ └───────┬───────┘  │
│     │            │                │          │
└─────┼────────────┼────────────────┼──────────┘
      │            │                │
      ▼            ▼                ▼
    CVM          FFO/Data         Market
   Adapter       Adapter          Adapter
```

---

# 5. Ports

The application layer SHALL depend on ports.

## 5.1 FII Registry Port

```python
class FiiRegistry:
    def resolve(self, ticker: str) -> FiiIdentity:
        ...
```

---

## 5.2 Financial Data Port

```python
class FiiFinancialRepository:
    def snapshot(
        self,
        identity: FiiIdentity,
        reference_date: date,
    ) -> FinancialSnapshot:
        ...
```

---

## 5.3 FFO Repository

```python
class FfoRepository:
    def get(
        self,
        identity: FiiIdentity,
        reference_date: date,
    ) -> FfoObservation:
        ...
```

---

## 5.4 Dividend Repository

```python
class DividendRepository:
    def get_12m(
        self,
        identity: FiiIdentity,
        reference_date: date,
    ) -> DividendObservation:
        ...
```

---

## 5.5 Market Data Repository

```python
class MarketDataRepository:
    def closing_price(
        self,
        ticker: str,
        reference_date: date,
    ) -> PriceObservation:
        ...
```

---

# 6. Domain Entities

## 6.1 FiiIdentity

```python
@dataclass(frozen=True)
class FiiIdentity:
    ticker: str
    cnpj: str
    cvm_code: str | None
    name: str
    fii_type: FiiType
```

---

## 6.2 FiiType

```python
class FiiType(Enum):
    BRICK = "brick"
    HYBRID = "hybrid"
    PAPER = "paper"
    UNKNOWN = "unknown"
```

Only:

```text
BRICK
HYBRID
```

are eligible for this pipeline.

---

# 7. Normalized Financial Snapshot

The central domain object SHALL be:

```python
@dataclass(frozen=True)
class FinancialSnapshot:
    ticker: str
    cnpj: str
    reference_date: date

    shares_outstanding: Decimal
    net_asset_value: Decimal

    ffo_12m: Decimal
    ffo_3m: Decimal

    dividends_12m: Decimal
```

The snapshot SHALL contain normalized values only.

No source-specific field names SHALL leak into this object.

---

# 8. Market Snapshot

```python
@dataclass(frozen=True)
class MarketSnapshot:
    ticker: str
    reference_date: date

    closing_price: Decimal
    price_date: date

    source: str
```

The selected price SHALL be:

> the latest valid closing price whose trading date is less than or equal to `reference_date`.

---

# 9. Raw Data Layer

The infrastructure layer SHALL preserve the original source payload whenever practical.

Recommended structure:

```text
data/
    raw/
        cvm/
            mensal/
            trimestral/
            anual/
            df/
        market/
        ffo/
        dividends/

    normalized/
        fii/
        financial/
        market/

    evidence/
```

Raw files SHALL NOT be modified after acquisition.

---

# 10. CVM Source

The primary regulatory source SHALL be the CVM Open Data Portal.

The CVM currently provides structured:

* FII Monthly Reports;
* FII Quarterly Reports;
* FII Annual Reports;
* FII Financial Statements.

The monthly FII dataset contains historical data and is updated weekly with possible resubmissions.

The monthly files are distributed by year under:

```text
FII/DOC/INF_MENSAL/DADOS/
```

including annual ZIP files.

The implementation SHALL avoid hardcoding individual file names beyond the source adapter.

---

# 11. CVM Adapter

The adapter SHALL expose:

```python
class CvmFiiAdapter:
    def monthly_reports(
        self,
        year: int,
    ) -> Iterable[RawMonthlyReport]:
        ...

    def quarterly_reports(
        self,
        year: int,
    ) -> Iterable[RawQuarterlyReport]:
        ...

    def annual_reports(
        self,
        year: int,
    ) -> Iterable[RawAnnualReport]:
        ...

    def financial_statements(
        self,
        year: int,
    ) -> Iterable[RawFinancialStatement]:
        ...
```

---

# 12. CVM Download Strategy

The adapter SHALL:

1. resolve the required years;
2. download the corresponding datasets;
3. calculate content hashes;
4. store the original archive;
5. extract it into the raw layer;
6. register acquisition metadata.

Example:

```text
Source:
CVM

Dataset:
INF_MENSAL

Year:
2026

DownloadedAt:
2026-09-09T...

SHA256:
...

SourceVersion:
2026-09-05
```

The source timestamp SHALL be retained.

---

# 13. Incremental Acquisition

FlowScope SHALL NOT download the entire historical CVM database for every analysis.

For a reference date `D`, the acquisition layer SHOULD initially inspect:

```text
year(D)
year(D - 1)
```

Additional years SHALL be loaded only if required.

For FFO 12M and dividend 12M, the minimum required period is:

```text
D - 12 months
```

plus enough additional history to resolve reporting periods and corrections.

---

# 14. CVM Reprocessing

Because CVM datasets can contain resubmissions, FlowScope SHALL treat the source as versioned.

For a logical observation:

```text
ticker
+
competence
+
document_type
```

the system SHALL select:

```text
latest valid submission
```

whose submission date is:

```text
<= reference_date
```

---

# 15. Temporal Rule

This is a critical invariant.

Suppose:

```text
reference_date = 2026-09-08
```

and:

```text
report competence = 2026-08
submission date = 2026-09-10
```

That report SHALL NOT be used.

The system SHALL behave as if the report did not exist at the reference date.

This prevents look-ahead bias.

---

# 16. Ticker Resolution

Ticker SHALL NOT be treated as the canonical identity.

Resolution:

```text
ticker
   ↓
CVM identity
   ↓
CNPJ
   ↓
fund identity
```

The registry SHOULD maintain:

```text
ticker
cnpj
cvm_code
fund_name
status
type
valid_from
valid_to
```

This is necessary because tickers may change.

---

# 17. Ticker Normalization

Input:

```text
"knri11"
"KNRI11"
" KNRI11 "
```

SHALL resolve to:

```text
KNRI11
```

Invalid formats SHALL be rejected.

Initial validation:

```regex
^[A-Z]{4}[0-9]{2}$
```

The regex is only syntactic validation; actual eligibility SHALL be resolved against the registry.

---

# 18. FII Classification

Classification SHALL be performed before financial analysis.

The system SHALL reject:

```text
PAPER
UNKNOWN
```

with:

```text
FII_NOT_ELIGIBLE
```

The classification source SHALL be recorded.

The system SHALL NOT infer:

```text
"brick"
```

from the fund name alone.

---

# 19. FFO Acquisition Strategy

FFO is the most sensitive part of this pipeline.

The domain SHALL define:

```python
@dataclass(frozen=True)
class FfoObservation:
    ffo_12m: Decimal
    ffo_3m: Decimal

    period_start_12m: date
    period_end_12m: date

    period_start_3m: date
    period_end_3m: date

    source: str
    methodology: str
```

---

# 20. FFO Source Contract

The FFO adapter SHALL explicitly declare its methodology:

```python
class FfoMethodology(Enum):
    SOURCE_REPORTED = "source_reported"
    DERIVED = "derived"
```

The first implementation SHOULD prefer:

```text
SOURCE_REPORTED
```

when the selected data provider publishes a defined FFO measure.

If FFO is derived, the adapter SHALL provide the complete derivation metadata.

---

# 21. FFO Must Not Be Guessed

The following SHALL be prohibited:

```text
FFO = net income
```

unless the methodology explicitly defines it.

Also prohibited:

```text
FFO = dividends
```

or:

```text
FFO = dividend × shares
```

or:

```text
FFO = arbitrary cash generation estimate
```

---

# 22. FFO Provider Adapter

To reproduce the original FlowScope table, the FFO source SHOULD be isolated:

```python
class FundamentalProvider:
    def ffo(
        self,
        ticker: str,
        reference_date: date,
    ) -> FfoObservation:
        ...
```

This allows the implementation to use the same provider methodology used to establish the project's golden dataset while keeping the CVM adapter independent.

---

# 23. FFO Reconciliation

When FFO is available from more than one source, FlowScope MAY perform reconciliation.

Example:

```text
CVM-derived FFO
Provider-reported FFO
```

The system SHALL NOT automatically choose one.

Instead:

```text
PRIMARY_FFO_SOURCE
SECONDARY_FFO_SOURCE
```

SHALL be configured.

The difference SHALL be calculated:

$$
FFODeviation =
\frac{|FFO_A - FFO_B|}
{\max(|FFO_A|, |FFO_B|)}
$$

If:

```text
FFODeviation > configured_threshold
```

the result SHALL receive:

```text
FFO_SOURCE_DISCREPANCY
```

---

# 24. Dividend Acquisition

The dividend repository SHALL return actual distributions.

```python
@dataclass(frozen=True)
class DividendObservation:
    total_12m: Decimal
    payments: tuple[DividendPayment, ...]
    source: str
```

```python
@dataclass(frozen=True)
class DividendPayment:
    ex_date: date | None
    payment_date: date
    amount_per_share: Decimal
```

---

# 25. Dividend Window

The default FlowScope definition SHALL use:

```text
payment_date <= reference_date
```

and:

```text
payment_date > reference_date - 12 months
```

Therefore:

$$
Dividends_{12M}
=
\sum Payments
$$

within the defined window.

The window convention SHALL be documented in the output metadata.

---

# 26. Market Price

The market adapter SHALL return:

```python
PriceObservation(
    ticker="HGBS11",
    price=Decimal("18.74"),
    trading_date=date(...),
    source="..."
)
```

The adapter SHALL resolve the latest trading session:

```text
trading_date <= reference_date
```

---

# 27. Price Source

The price adapter SHALL be replaceable.

Example:

```text
MarketDataProvider
├── ProviderA
├── ProviderB
└── CachedProvider
```

The FlowScope domain SHALL not know which provider supplied the price.

---

# 28. Market Price Validation

The adapter SHALL reject:

* zero price;
* negative price;
* missing price;
* future price.

It SHALL additionally record:

```text
price_date
reference_date
```

so stale data can be identified.

---

# 29. Financial Snapshot Builder

The application service SHALL combine:

```text
FiiIdentity
MarketSnapshot
FinancialSnapshot
FfoObservation
DividendObservation
```

into:

```python
@dataclass(frozen=True)
class FiiAnalysisInput:
    identity: FiiIdentity
    market: MarketSnapshot
    financial: FinancialSnapshot
    ffo: FfoObservation
    dividends: DividendObservation
```

This object becomes the only input to the metric engine.

---

# 30. Metric Engine

The metric engine SHALL contain pure functions.

## Market Value

$$
MV = Price \times Shares
$$

```python
def market_value(data):
    return data.market.price * data.financial.shares_outstanding
```

---

## FFO Yield

$$
FFOYield =
\frac{FFO_{12M}}{MV}
$$

---

## P/FFO

$$
P/FFO =
\frac{MV}{FFO_{12M}}
$$

---

## Dividend Yield

$$
DY =
\frac{Dividends_{12M}}{MV}
$$

---

## P/VP

$$
P/VP =
\frac{MV}{NAV}
$$

---

# 31. FFO Momentum

The engine SHALL calculate:

$$
FFO_{3MAnnualized}
=
FFO_{3M}\times4
$$

and:

$$
Momentum =
\frac{FFO_{3MAnnualized}}
{FFO_{12M}}-1
$$

---

# 32. Momentum Classification

Configuration:

```yaml
ffo_momentum:
  strong_growth: 0.20
  growth: 0.05
  stable_lower: -0.05
  strong_decline: -0.20
```

Rules:

```text
>= +20%       STRONG_GROWTH
>= +5%        GROWTH
> -5%         STABLE
>= -20%       DECLINE
< -20%        STRONG_DECLINE
```

The classifier SHALL be pure.

---

# 33. Important Negative FFO Rule

If:

```text
FFO_12M <= 0
```

then:

```text
FFO_YIELD = null
P_FFO = null
```

and:

```text
FFO_MOMENTUM = null
```

unless a dedicated negative-FFO methodology is later specified.

---

# 34. P/FFO Consistency Check

The engine SHALL verify:

$$
P/FFO =
\frac{1}{FFOYield}
$$

within the configured numerical tolerance.

Failure:

```text
P_FFO_INCONSISTENCY
```

---

# 35. Data Quality Model

```python
class DataQuality(Enum):
    COMPLETE = "complete"
    WARNING = "warning"
    PARTIAL = "partial"
    INVALID = "invalid"
```

Warnings SHALL include:

```text
STALE_PRICE
FFO_SOURCE_DISCREPANCY
HIGH_DISTRIBUTION_VS_FFO
NEGATIVE_RECENT_FFO
STRONG_FFO_DECLINE
```

---

# 36. Distribution-vs-FFO Warning

The system SHALL calculate:

$$
FFOPayout =
\frac{Dividends_{12M}}
{FFO_{12M}}
$$

If:

$$
DividendYield > 1.25 \times FFOYield
$$

then:

```text
HIGH_DISTRIBUTION_VS_FFO
```

SHALL be emitted.

This is a warning, not an investment recommendation.

---

# 37. Evidence Model

Every metric SHALL produce:

```python
@dataclass(frozen=True)
class MetricEvidence:
    metric: str
    value: Decimal | None

    formula: str

    inputs: dict[str, Decimal | str]

    sources: tuple[str, ...]

    reference_date: date

    calculation_version: str
```

Example:

```json
{
  "metric": "FFO_YIELD",
  "value": "0.0816",
  "formula": "ffo_12m / market_value",
  "inputs": {
    "ffo_12m": "220777000",
    "market_value": "2705000000"
  },
  "sources": [
    "FFO_PROVIDER",
    "MARKET_PROVIDER"
  ],
  "reference_date": "2026-09-08",
  "calculation_version": "1.0"
}
```

---

# 38. Analysis Result

The final domain object SHALL be:

```python
@dataclass(frozen=True)
class FiiAnalysisResult:
    ticker: str
    reference_date: date

    price: Decimal
    price_date: date

    ffo_yield: Decimal | None
    dividend_yield: Decimal | None
    p_ffo: Decimal | None
    p_vp: Decimal | None

    ffo_12m: Decimal | None
    ffo_3m: Decimal | None
    ffo_momentum: Decimal | None
    ffo_trend: FfoTrend | None

    warnings: tuple[str, ...]

    quality: DataQuality

    evidence: tuple[MetricEvidence, ...]
```

---

# 39. Batch Analysis

For:

```text
KNRI11
HSML11
XPML11
...
HGLG11
```

the use case SHALL be:

```python
analyze_many(
    tickers,
    reference_date,
)
```

Each ticker SHALL be processed independently.

A failure for one ticker SHALL NOT invalidate the others.

Example:

```text
KNRI11   COMPLETE
HSML11   COMPLETE
XPML11   COMPLETE
HCRI11   WARNING
UNKNOWN  INVALID
```

---

# 40. Batch Result Contract

```python
@dataclass(frozen=True)
class BatchAnalysisResult:
    reference_date: date
    results: tuple[FiiAnalysisResult, ...]
```

The output SHALL preserve input order unless an explicit sort is requested.

---

# 41. Table Projection

The presentation layer SHALL transform:

```text
FiiAnalysisResult
```

into:

```text
FiiTableRow
```

```python
@dataclass(frozen=True)
class FiiTableRow:
    ticker: str
    ffo_yield: str
    dividend_yield: str
    p_ffo: str
    p_vp: str
    ffo_trend: str
```

Formatting SHALL occur only here.

---

# 42. Formatting Rules

Internal:

```text
0.08163472
```

Presentation:

```text
8,16%
```

Internal:

```text
12.24783
```

Presentation:

```text
12,25x
```

The formatter SHALL never modify the underlying analytical value.

---

# 43. Cache

The acquisition layer SHALL use content-addressed or key-addressed caching.

Suggested key:

```text
source
dataset
period
source_version
```

For market data:

```text
provider
ticker
trading_date
```

For analysis:

```text
ticker
reference_date
calculation_version
```

---

# 44. Analysis Cache

A completed analysis MAY be cached.

Cache key:

```text
FII_ANALYSIS:
    ticker
    reference_date
    source_snapshot_hash
    calculation_version
```

The source snapshot hash is important.

If an upstream CVM report is corrected, the hash changes and the analysis becomes stale automatically.

---

# 45. Reproducibility

Every completed analysis SHALL be reproducible from:

```text
reference_date
+
source snapshots
+
source hashes
+
configuration
+
calculation version
```

The system SHALL NOT require live internet access to reproduce an already persisted analysis.

---

# 46. Offline Replay

FlowScope SHALL support:

```text
--offline
```

mode.

Example:

```bash
flowscope fii analyze KNRI11 --date 2026-09-08 --offline
```

If all required source snapshots are cached:

```text
SUCCESS
```

Otherwise:

```text
MISSING_SOURCE_SNAPSHOT
```

SHALL be returned.

---

# 47. CLI Contract

Recommended commands:

```bash
flowscope fii analyze KNRI11
```

```bash
flowscope fii analyze KNRI11 --date 2026-09-08
```

```bash
flowscope fii compare KNRI11 HSML11 XPML11
```

```bash
flowscope fii compare-list fiis.txt
```

```bash
flowscope fii explain KNRI11
```

The `explain` command SHALL expose evidence.

---

# 48. Example CLI Output

```text
FII FUNDAMENTAL ANALYSIS
Reference date: 2026-09-08

Ticker       FFO Yield    DY       P/FFO    P/VP    FFO Trend
----------------------------------------------------------------
KNRI11         7.33%      6.8%     13.64x    0.96   ↘ Decline
HSML11         8.28%      8.5%     12.08x    0.78   ↗ Growth
XPML11         7.87%      8.6%     12.71x    0.95   ↘ Decline
...
```

---

# 49. Explain Output

Example:

```bash
flowscope fii explain HGBS11
```

SHALL produce:

```text
HGBS11
Reference date: 2026-09-08

PRICE
  R$ 18.74
  Source: MARKET_PROVIDER
  Date: 2026-09-08

FFO 12M
  R$ 220,777,000
  Source: FFO_PROVIDER

MARKET VALUE
  R$ 2,705,xxx,xxx
  Formula:
    price × shares

FFO YIELD
  8.16%
  Formula:
    FFO 12M / Market Value

P/FFO
  12.25x
  Formula:
    Market Value / FFO 12M

P/VP
  0.92x
  Formula:
    Market Value / NAV

FFO MOMENTUM
  +15.6%
  Classification:
    GROWTH
```

---

# 50. Error Taxonomy

Errors SHALL use stable identifiers.

```text
FII_NOT_FOUND
FII_NOT_ELIGIBLE
CVM_DATA_UNAVAILABLE
CVM_REPORT_NOT_FOUND
CVM_REPORT_INVALID
CVM_REPROCESSING_CONFLICT
PRICE_NOT_FOUND
PRICE_STALE
FFO_NOT_FOUND
FFO_INVALID
FFO_SOURCE_DISCREPANCY
DIVIDEND_DATA_NOT_FOUND
NAV_NOT_FOUND
INVALID_REFERENCE_DATE
DATA_INCONSISTENCY
MISSING_SOURCE_SNAPSHOT
```

---

# 51. Retry Policy

Network acquisition SHALL use bounded retry.

Recommended:

```text
attempts = 3
backoff = exponential
```

Example:

```text
1s
2s
4s
```

Retry SHALL apply only to transient errors.

It SHALL NOT retry:

```text
404
invalid ticker
invalid dataset
schema validation failure
```

---

# 52. Source Schema Validation

Every downloaded dataset SHALL be validated before ingestion.

Validation:

```text
expected columns
data types
date formats
numeric formats
required fields
encoding
```

If the schema changes:

```text
SOURCE_SCHEMA_CHANGED
```

SHALL be raised.

The system SHALL NOT attempt to guess column mappings automatically.

---

# 53. Source Schema Version

Each adapter SHALL declare:

```python
SOURCE_SCHEMA_VERSION = "YYYY-MM-DD"
```

or an equivalent explicit version.

Changes to source schemas SHALL require an adapter version update.

---

# 54. Golden Dataset

The repository SHALL contain a frozen dataset for:

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

The golden dataset SHALL contain:

```text
reference_date
price
shares
NAV
FFO 12M
FFO 3M
dividends 12M
expected metrics
expected trend
```

---

# 55. Golden Test

Example:

```python
def test_hgbs11_analysis():
    result = analyze(
        load_fixture("HGBS11-2026-09-08.json")
    )

    assert result.ffo_yield == Decimal("0.0816")
    assert result.p_ffo == Decimal("12.25")
    assert result.p_vp == Decimal("0.92")
```

The fixture SHALL be independent of live providers.

---

# 56. Property Tests

The metric engine SHALL include invariant tests.

```python
def test_p_ffo_inverse_of_ffo_yield(snapshot):
    assert approx(
        p_ffo(snapshot) * ffo_yield(snapshot),
        Decimal("1")
    )
```

---

# 57. Temporal Tests

The system SHALL test look-ahead prevention.

Example:

```text
reference_date = 2026-09-08

report submitted = 2026-09-10
```

Expected:

```text
report excluded
```

---

# 58. Reprocessing Tests

Given:

```text
version A:
submission = 2026-09-01

version B:
submission = 2026-09-07
```

and:

```text
reference_date = 2026-09-08
```

Expected:

```text
version B
```

For:

```text
reference_date = 2026-09-05
```

Expected:

```text
version A
```

---

# 59. Deterministic Replay Test

The following SHALL produce byte-equivalent serialized results:

```text
run #1
run #2
```

using:

```text
same source snapshots
same configuration
same calculation version
```

---

# 60. Decimal Arithmetic

Financial calculations SHALL use:

```python
decimal.Decimal
```

and SHALL NOT use binary floating point for final monetary calculations.

This avoids differences such as:

```text
0.1 + 0.2 != 0.3
```

in binary floating-point arithmetic.

---

# 61. Rounding Policy

No rounding SHALL occur during intermediate calculations.

Example:

```text
FFO
÷
Market Value
```

shall use full available precision.

Rounding SHALL occur only in:

```text
presentation
golden expected display values
```

unless a source-specific financial convention explicitly requires otherwise.

---

# 62. Configuration

Thresholds SHALL be externalized.

Example:

```yaml
fii_analysis:
  ffo_momentum:
    strong_growth: 0.20
    growth: 0.05
    stable_lower: -0.05
    strong_decline: -0.20

  distribution_warning:
    dividend_to_ffo_ratio: 1.25

  price:
    max_staleness_days: 5
```

Configuration SHALL be versioned.

---

# 63. Dependency Injection

The use case SHALL receive interfaces:

```python
AnalyzeFiiUseCase(
    fii_registry,
    financial_repository,
    ffo_repository,
    dividend_repository,
    market_repository,
)
```

Tests SHALL inject deterministic fixtures.

---

# 64. Recommended FlowScope Modules

Given the existing FlowScope architecture, the recommended structure is:

```text
flowscope/
│
├── domain/
│   └── fii/
│       ├── entities.py
│       ├── value_objects.py
│       ├── metrics.py
│       ├── trends.py
│       ├── classification.py
│       └── errors.py
│
├── application/
│   └── fii/
│       ├── analyze.py
│       ├── compare.py
│       └── explain.py
│
├── infrastructure/
│   └── fii/
│       ├── cvm/
│       │   ├── client.py
│       │   ├── adapter.py
│       │   ├── parser.py
│       │   └── repository.py
│       │
│       ├── market/
│       │   ├── client.py
│       │   └── repository.py
│       │
│       ├── ffo/
│       │   ├── provider.py
│       │   └── repository.py
│       │
│       └── dividends/
│           ├── provider.py
│           └── repository.py
│
└── presentation/
    └── fii/
        ├── table.py
        └── formatter.py
```

---

# 65. Dependency Direction

The dependency graph SHALL remain:

```text
presentation
      ↓
application
      ↓
domain
      ↑
infrastructure
```

Infrastructure SHALL implement domain/application ports.

Domain SHALL NOT import infrastructure.

---

# 66. Source Provider Abstraction

The implementation SHOULD support:

```text
             ┌──────────────────┐
             │ FundamentalPort  │
             └────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   CVM-derived    Provider A    Provider B
```

This allows FlowScope to evolve its data sources without changing the metric engine.

---

# 67. Important Distinction: Regulatory Data vs Market Data

The system SHALL maintain two temporal axes:

```text
event/reference period
submission/publication date
```

For example:

```text
Competence:
2026-08

Submitted:
2026-09-07
```

Both SHALL be retained.

This prevents accidental look-ahead.

---

# 68. Data Lineage

Every final metric SHALL be traceable through:

```text
Metric
  ↓
Calculation
  ↓
Normalized input
  ↓
Raw observation
  ↓
Source document
  ↓
Source hash
```

This lineage SHALL be represented by the evidence model.

---

# 69. Analysis Fingerprint

Each analysis SHALL generate:

```text
analysis_hash
```

based on:

```text
ticker
reference_date
normalized_snapshot
configuration_version
calculation_version
source_hashes
```

Example:

```text
analysis_hash =
SHA256(canonical_json(...))
```

This allows two runs to be compared efficiently.

---

# 70. Idempotency

Running:

```bash
flowscope fii analyze HGBS11 --date 2026-09-08
```

twice SHALL NOT create duplicate logical observations.

The persisted result SHALL be keyed by:

```text
ticker
reference_date
calculation_version
analysis_hash
```

---

# 71. Observability

The pipeline SHOULD log:

```text
source acquisition
source cache hit
source cache miss
ticker resolution
report resolution
FFO resolution
price resolution
metric calculation
validation
warnings
```

Example:

```text
[INFO] HGBS11 resolved to CVM identity ...
[INFO] CVM monthly snapshot loaded
[INFO] FFO source resolved
[INFO] Market price resolved: 18.74
[INFO] FFO Yield calculated: 8.16%
[WARN] Dividend/FFO ratio above threshold
```

---

# 72. Performance

The implementation SHOULD:

* cache downloaded CVM datasets;
* avoid repeated extraction of unchanged ZIPs;
* cache normalized observations;
* batch ticker resolution;
* batch market requests where supported;
* calculate metrics locally.

The metric engine SHALL be computationally trivial compared with acquisition.

---

# 73. Failure Isolation

If:

```text
HGBS11
```

fails FFO acquisition, FlowScope SHALL return:

```text
HGBS11 = INVALID
```

but continue:

```text
KNRI11 = COMPLETE
HSML11 = COMPLETE
XPML11 = COMPLETE
...
```

---

# 74. No Partial Silent Results

The system SHALL NOT output:

```text
HGBS11
FFO Yield = 8.16%
P/FFO = N/A
P/VP = 0.92
```

without identifying the missing P/FFO reason.

Instead:

```text
P/FFO = N/A
warning = FFO_NOT_AVAILABLE
```

---

# 75. API Contract

Future REST API MAY expose:

```http
GET /api/fii/{ticker}/analysis
```

Parameters:

```text
date
```

Response:

```json
{
  "ticker": "HGBS11",
  "reference_date": "2026-09-08",
  "metrics": {
    "ffo_yield": 0.0816,
    "dividend_yield": 0.084,
    "p_ffo": 12.25,
    "p_vp": 0.92
  },
  "ffo_trend": {
    "change": 0.1559,
    "classification": "GROWTH"
  },
  "quality": "COMPLETE",
  "warnings": []
}
```

---

# 76. CLI/GUI Independence

The analysis engine SHALL NOT depend on the FlowScope GUI.

The same use case SHALL support:

```text
CLI
GUI
REST
batch jobs
tests
```

---

# 77. Acceptance Scenario

Given:

```text
ticker = HGBS11
reference_date = 2026-09-08
```

and the frozen golden source snapshot, FlowScope SHALL produce:

```text
FFO Yield ≈ 8.16%
P/FFO ≈ 12.25x
P/VP ≈ 0.92x
Dividend Yield ≈ 8.4%
FFO Trend = GROWTH
```

within the configured presentation precision.

---

# 78. Acceptance Scenario — Look-Ahead

Given:

```text
reference_date = 2026-09-08
```

a report submitted:

```text
2026-09-09
```

SHALL NOT affect the result.

---

# 79. Acceptance Scenario — Reprocessing

Given two versions:

```text
V1 submitted 2026-09-01
V2 submitted 2026-09-07
```

then:

```text
reference_date = 2026-09-06
```

SHALL use V1.

While:

```text
reference_date = 2026-09-08
```

SHALL use V2.

---

# 80. Acceptance Scenario — Invalid FII

Given:

```text
ticker = UNKNOWN11
```

the system SHALL return:

```text
FII_NOT_FOUND
```

and SHALL NOT query downstream financial sources.

---

# 81. Acceptance Scenario — Paper FII

Given a known paper FII:

```text
ticker = <paper_fii>
```

the system SHALL return:

```text
FII_NOT_ELIGIBLE
```

before executing the fundamental metric pipeline.

---

# 82. Acceptance Scenario — Negative FFO

Given:

```text
FFO_12M < 0
```

the result SHALL be:

```text
FFO Yield = N/A
P/FFO = N/A
FFO Trend = N/A
```

and SHALL contain:

```text
NEGATIVE_FFO
```

---

# 83. Acceptance Scenario — Distribution Anomaly

Given:

```text
Dividend Yield = 12.8%
FFO Yield = 5.66%
```

the result SHALL contain:

```text
HIGH_DISTRIBUTION_VS_FFO
```

The warning SHALL NOT modify either metric.

---

# 84. Versioning

This RFC SHALL have a calculation version:

```text
FII_ANALYSIS_V1
```

Any change to:

* formula;
* threshold;
* source precedence;
* temporal semantics;
* rounding affecting analytical values;

SHALL increment the calculation version.

---

# 85. Backward Compatibility

Changes to acquisition adapters SHALL NOT change historical results when the same source snapshot remains available.

Changes to calculation logic SHALL produce a new calculation version.

Example:

```text
FII_ANALYSIS_V1
FII_ANALYSIS_V2
```

Both MAY coexist for historical comparison.

---

# 86. Test Matrix

Minimum test coverage:

| Area                     | Required |
| ------------------------ | -------: |
| Ticker normalization     |        ✓ |
| FII classification       |        ✓ |
| CVM parsing              |        ✓ |
| CVM resubmission         |        ✓ |
| Reference-date filtering |        ✓ |
| Market price             |        ✓ |
| FFO acquisition          |        ✓ |
| Dividend acquisition     |        ✓ |
| FFO Yield                |        ✓ |
| Dividend Yield           |        ✓ |
| P/FFO                    |        ✓ |
| P/VP                     |        ✓ |
| FFO Momentum             |        ✓ |
| Warning generation       |        ✓ |
| Decimal precision        |        ✓ |
| Cache                    |        ✓ |
| Replay                   |        ✓ |
| Golden dataset           |        ✓ |
| Batch isolation          |        ✓ |

---

# 87. Definition of Done

The implementation SHALL be considered complete when:

* [ ] `KNRI11` can be analyzed from end to end;
* [ ] all 12 reference FIIs have golden fixtures;
* [ ] CVM acquisition is cached;
* [ ] reference-date filtering is implemented;
* [ ] resubmission resolution is implemented;
* [ ] market price adapter is implemented;
* [ ] FFO adapter is implemented;
* [ ] dividend adapter is implemented;
* [ ] normalized snapshot exists;
* [ ] metric engine is pure;
* [ ] evidence is generated;
* [ ] warnings are deterministic;
* [ ] CLI command works;
* [ ] batch analysis works;
* [ ] offline replay works;
* [ ] golden tests pass;
* [ ] property/invariant tests pass;
* [ ] no domain code imports infrastructure;
* [ ] calculation version is persisted.

---

# 88. Implementation Sequence

The recommended implementation order is:

```text
Phase 1
  Domain models
  Metric engine
  Trend engine
  Tests

Phase 2
  Golden fixtures
  Deterministic analysis
  Table projection

Phase 3
  CVM adapter
  Raw-data cache
  Normalization

Phase 4
  Market adapter

Phase 5
  FFO provider

Phase 6
  Dividend provider

Phase 7
  Evidence / lineage

Phase 8
  CLI integration

Phase 9
  Batch analysis

Phase 10
  Offline replay
```

This order intentionally places the deterministic calculation engine before external integration.

---

# 89. Architectural Decision

FlowScope SHALL treat the FII fundamental-analysis feature as a:

> **Data Pipeline + Deterministic Measurement Engine**

rather than as a scraping feature.

The architecture SHALL therefore be:

```text
Sources
   ↓
Adapters
   ↓
Raw Data
   ↓
Normalization
   ↓
Canonical FII Snapshot
   ↓
Pure Metrics
   ↓
Validation
   ↓
Evidence
   ↓
Presentation
```

This permits replacement of any external provider without changing the analytical semantics.

---

# 90. Final Operational Contract

The complete feature SHALL satisfy:

```text
INPUT

ticker
reference_date


↓

IDENTITY

ticker → CNPJ → CVM identity


↓

ELIGIBILITY

BRICK / HYBRID


↓

SOURCE RESOLUTION

CVM
Market
FFO
Dividends


↓

TEMPORAL RESOLUTION

latest valid information
available at reference_date


↓

NORMALIZATION

canonical snapshot


↓

CALCULATION

FFO Yield
Dividend Yield
P/FFO
P/VP
FFO Momentum


↓

VALIDATION

invariants
source consistency
data quality


↓

EVIDENCE

formula
inputs
sources
dates
versions


↓

OUTPUT

deterministic FII analysis
```

The implementation SHALL never cross these boundaries implicitly.

---

# 91. Reference Sources

The primary regulatory data source is the **CVM Dados Abertos — FII Informe Mensal Estruturado**, which provides the monthly FII reports, historical data and periodic updates including resubmissions.

The CVM also exposes structured FII quarterly reports, annual reports and financial statements through its FII datasets.

The annual ZIP files are available through the CVM data repository, including current historical datasets.

These sources SHALL be treated as external infrastructure and SHALL NOT leak into the FlowScope domain model.

