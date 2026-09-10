## Context

O FlowScope segue Clean Architecture em 4 camadas (`domain/`, `application/`, `infrastructure/`, `presentation/`) com protocolos para desacoplamento. A GUI usa Tkinter com um `ttk.Notebook` principal ("Análise Geral" / "Análise do Ticker"); a aba "Análise Geral" tem um sub-notebook (`_general_notebook`) construído em `_build_general_tabs()` (`presentation/gui/app_tab_layout.py`), hoje com VWAP, Quadrantes e Dominância do Pregão.

As changes `structured-earnings` (RFC-001, entidade `Provento` com `data_base`, `data_pagamento`, `valor_por_unidade`, `tipo`) e `regulacao-mercado` (`code-cvm-resolution`) estão em aberto e fornecem, respectivamente, os dados de provento e a identidade CVM. As RFC-006/007 definem o motor determinístico de métricas FII e exigem CVM como fonte primária, `decimal.Decimal`, funções puras e evidência por métrica.

## Goals / Non-Goals

**Goals:**
- Adicionar a sub-aba "Fundamentos" com uma tabela por ticker da watchlist.
- Separar claramente as três etapas de aquisição/normalização/cálculo/apresentação (princípio 3.5 da RFC-007).
- Manter o domínio de cálculo (classificação, tendência de dividendo, métricas FII) puro e independente de infraestrutura.
- Entregar em duas fases: A (identidade + dividendos) e B (métricas FFO).

**Non-Goals:**
- Dividendos de ações/JCP na Fase A (fonte é endpoint B3 distinto, postergado).
- Recomendação de compra, valuation, preço-alvo ou qualquer interpretação qualitativa.
- CLI nesta change (o escopo é a GUI; o domínio é reutilizável por CLI futura).
- Async/paralelismo na aquisição.

## Decisions

### 1. Estrutura em camadas espelhando a RFC-007

O domínio não conhece CVM, HTTP, HTML ou scraping. As funções de cálculo são puras e operam sobre um snapshot normalizado.

```
domain/
  fii/
    classification.py     # TipoAtivo, SubTipoFii, SubTipoAcao, TaxonomiaFii
    dividends.py          # UltimoDividendo, TendenciaDividendo (banda ±5%)
    metrics.py            # ffo_yield, dividend_yield, p_ffo, p_vp, ffo_momentum
    classification_faixas.py  # classe por nº de cotistas e por patrimônio
application/
  fundamental_analysis.py # FundamentalAnalysisUseCase (orquestra portas)
  fundamental_ports.py    # FiiFundamentalRepository, FfoProvider, MarketPricePort
infrastructure/
  cvm/                    # CVMAdapter (NAV, cotas, cotistas)
  ffo/                    # FundamentusProvider (FFO 12m/3m)
presentation/gui/
  charts/fundamental_table.py  # FundamentalTablePanel (ttk.Treeview)
```

**Alternativa considerada:** um único módulo monolítico no estilo do RFC-001 original — rejeitado por violar a Clean Architecture do projeto.

### 2. Classificação híbrida (ticker sintático + codeCVM + taxonomia)

- **Tipo (ação/FII/ETF/BDR)** e **sub-tipo de ação (ordinária/preferencial/ETF)** são derivados sintaticamente do ticker (dígito/segmento) e validados com `code-cvm-resolution`.
- **Sub-tipo de FII** (tijolo/papel/híbrido/fiagro/fiinfra) vem de uma **taxonomia versionada** (`TaxonomiaFii`), um mapa estático `ticker → sub-tipo` versionado no repositório, conforme sancionado pela RFC-006 ("taxonomia previamente versionada").

**Alternativa considerada:** extrair sub-tipo de FII de fonte dinâmica B3/CVM — rejeitado porque a classificação tijolo/papel/fiagro não está estruturada de forma confiável na B3 e o custo de manutenção de uma taxonomia é menor que o de um parser frágil.

### 3. Tendência do dividendo = último vs. anterior, banda ±5%

`TendenciaDividendo` compara o último `Provento` de tipo `Rendimento` com o anterior, usando banda configurável (padrão ±5%, espelhando a RFC-006): `SUBINDO` se `último ≥ anterior×1,05`, `CAINDO` se `último ≤ anterior×0,95`, senão `MANTEVE`; `N/A` quando não há dividendo anterior. Amortização é excluída.

**Alternativa considerada:** comparar com a média 12m (análogo ao FFO Momentum) — descartado pelo usuário em favor da comparação direta último vs. anterior.

### 4. Preço de fechamento reusado dos dados B3 existentes

O `MarketPricePort` é satisfeito pelos dados de negociação B3 já carregados (campo `LastPric`), evitando um novo adapter de mercado. A RFC-007 exige apenas "último fechamento até reference_date", que já está disponível.

### 5. FFO via Fundamentus (provider) e NAV/cotas via CVM

- **FFO 12m/3m** vem de um `FundamentalProvider` (Fundamentus), com metodologia `SOURCE_REPORTED`, isolado atrás de `FfoProvider` (RFC-007 §22).
- **NAV (PL), nº de cotas e nº de cotistas** vêm de um `CVMAdapter` (informe mensal/trimestral estruturado), fiel ao princípio "CVM é fonte primária" (RFC-006 R3).

**Alternativa considerada:** obter `patrimonioLiquido` do informe-mensal B3 (change em aberto) — rejeitado para NAV por desviar do requisito CVM-primária da RFC.

### 6. Modelo de evidência por métrica

Cada métrica produz um `MetricEvidence` (metric, value, formula, inputs, sources, reference_date, calculation_version), permitindo auditoria "por que 8,16%?" sem interpretação humana (RFC-006 §3, RFC-007 §37).

### 7. Faseamento da entrega

- **Fase A**: sub-aba + identidade + classificação + dividendos (todos os tickers; ações/ETF com `N/A` nas colunas de dividendo).
- **Fase B**: métricas FFO (apenas FII elegível), com adapter CVM + provedor Fundamentus.

## Risks / Trade-offs

- **[Risco] `structured-earnings` e `regulacao-mercado` ainda não implementadas (0/xx tarefas)** → A Fase A depende de `Provento`/`code-cvm-resolution`. Mitigação: definir portas (`FiiFundamentalRepository`) para permitir começar com fixtures determinísticos e integrar as fontes quando prontas.
- **[Risco] Mudança no HTML/endpoints do provedor de FFO e da CVM** → Adapters isolados com `SOURCE_SCHEMA_VERSION`; falha de aquisição marca o ticker como `N/A`/`INVALID` sem derrubar os demais (batch isolation, RFC-007 §73).
- **[Risco] Taxonomia de sub-tipo FII desatualizada** → Taxonomia versionada explicitamente; ticker não mapeado recebe sub-tipo `DESCONHECIDO` (exibido, nunca inferido do nome).
- **[Trade-off] Fase A sem dividendos de ações** → Colunas de dividendo ficam `N/A` para ações; extensão futura adiciona o endpoint de proventos de ações.
