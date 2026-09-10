## Why

As colunas `FFO Yield`, `P/FFO` e `FFO Trend` da sub-aba "Fundamentos" têm o Fundamentus como fonte primária (change `fundamentus-fundamental-provider`). A RFC-010 define um motor determinístico que **calcula** o FFO a partir dos componentes econômicos estruturados da CVM (Informe Trimestral), reconciliados com as Demonstrações Financeiras (DFIN), classificando cada componente como recorrente, fair value, alienação ou não recorrente. Esta change é a terceira fase do programa e entrega esse motor como **fallback** de FFO, quando o Fundamentus falhar ou não trouxer o dado.

## What Changes

- Nova camada de aquisição CVM do Informe Trimestral Estruturado e das Demonstrações Financeiras (DFIN) por CNPJ, sobre o pipeline de dados abertos da CVM.
- Classificador determinístico de componentes de resultado (`RECURRING`, `FAIR_VALUE`, `DISPOSAL`, `NON_RECURRING`, `UNKNOWN`), com regra conservadora: apenas `RECURRING` entra no FFO.
- Motor de FFO: FFO mensal → FFO 12m → FFO por cota (média ponderada de cotas) → FFO Yield e P/FFO, com qualidade (`HIGH`/`MEDIUM`/`LOW`) e proveniência por componente.
- Reconciliação com DFIN/Informe Trimestral, gerando warning quando a diferença exceder o limite configurável.
- O FFO calculado passa a atuar como fallback do Fundamentus: quando o Fundamentus não fornece FFO, as métricas usam o motor determinístico.
- Integração com o motor de métricas existente, definindo uma única fonte de verdade para `FFO Yield` e `P/FFO`.

## Capabilities

### New Capabilities

- `cvm-quarterly-fund-data`: Aquisição determinística do Informe Trimestral Estruturado e das DFIN de FIIs por CNPJ, com schema versionado, preservação bruta e normalização dos componentes de resultado.
- `deterministic-ffo-engine`: Cálculo determinístico, auditável e versionado do FFO (mensal, 12m, por cota, Yield e P/FFO) a partir de componentes classificados, com proveniência, qualidade e reconciliação.

### Modified Capabilities

<!-- Nenhuma: a exibição é consequência do motor existente; o FFO calculado é uma fonte de fallback. -->

## Impact

- **Código afetado**: novo módulo de aquisição CVM trimestral/DFIN, `domain/ffo/` (componentes, classificador, motor), `application/fundamental_analysis.py` (FFO calculado), remoção/substituição de `infrastructure/fii/ffo_provider.py`, `domain/fii/metrics.py` (fonte única de FFO Yield/P/FFO).
- **Dados**: `inf_trimestral_fii_<ano>.zip` e `dfin_fii_<ano>.csv`, com hash/metadados sob `~/.cache/flowscope/`.
- **Dependências**: `b3-fii-identity-and-dividends` (identidade/CNPJ) e `cvm-monthly-fund-data` (pipeline CVM e patrimônio/cotas).
- **Escopo**: não usa FFO divulgado por gestores; nenhum LLM participa do cálculo em produção.
