## Why

A coluna `P/VP` da sub-aba "Fundamentos" tem o Fundamentus como fonte primária (change `fundamentus-fundamental-provider`), mas depende de patrimônio líquido, número de cotas e cotistas quando o Fundamentus falhar ou não trouxer o dado. Hoje um `CvmFiiAdapter` lê o Informe Mensal da CVM com o schema legado (`CNPJ_FUNDO`, `QUANT_COTA`) e não é populado em produção. A RFC-009 define um pipeline determinístico por CNPJ sobre os dados abertos da CVM, com versionamento de schema, reapresentações e hash. Esta change é a segunda fase do programa: entrega a extração do Informe Mensal Estruturado da CVM como fonte de **fallback** para patrimônio/cotas/cotistas e `P/VP`, deixando `FFO Yield`, `P/FFO` e `FFO Trend` para a fase do motor de FFO (RFC-010).

## What Changes

- Nova camada de aquisição CVM (`dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL`) por CNPJ: download do ZIP anual, extração dos CSVs, descoberta/versionamento de schema, filtro por CNPJ e competência, seleção da reapresentação mais recente e preservação de hash/metadados.
- Resolução de identidade (`FundIdentity`): ticker → CNPJ + idFNET + codeCVM, combinando a identidade B3 (change anterior) com o cadastro CVM.
- Normalização de patrimônio (`PatrimonioFii`): `VL_PATRIM_LIQ`, `QT_COTA`, `NR_COTST` a partir do schema 2025+, com aliases legados (`CNPJ_Fundo`, `QUANT_COTA`).
- Atualização/encapsulamento do `CvmFiiAdapter` existente para consumir o novo repositório, removendo o acoplamento ao schema antigo.
- O patrimônio da CVM passa a ser usado como fallback para `P/VP` quando o Fundamentus não fornecer o dado; `FFO Yield`, `P/FFO` e `FFO Trend` permanecem `N/A`.

## Capabilities

### New Capabilities

- `cvm-monthly-fund-data`: Aquisição determinística do Informe Mensal Estruturado da CVM por CNPJ (dados abertos anuais), com schema versionado, tratamento de reapresentações, hash/metadados e normalização de patrimônio/cotas/cotistas para as métricas fundamentalistas.

### Modified Capabilities

<!-- Nenhuma: a exibição de P/VP é consequência do provider e do motor existentes. -->

## Impact

- **Código afetado**: `infrastructure/fii/cvm.py` (repositório/serviço CVM por CNPJ), novo módulo de download/schema CVM, `infrastructure/fii/fundamental_repository.py` (patrimônio via novo provider), `application/fundamental_analysis.py` (P/VP).
- **Dados**: arquivos anuais `inf_mensal_fii_<ano>.zip`; preservação bruta e metadados sob `~/.cache/flowscope/`.
- **Dependências**: mantém `zipfile`+`csv` da stdlib (sem `pandas`); reusa `B3Fund`/identidade da change `b3-fii-identity-and-dividends`.
- **Escopo faseado**: `FFO Yield`, `P/FFO` e `FFO Trend` (RFC-010) permanecem `N/A` nesta change.
