## Why

O número de cotistas, o patrimônio líquido e o VP/Cota da tabela de Fundamentos nunca são preenchidos em produção. O `CvmMonthlyPatrimonioSource` não lê o layout atual do dataset da CVM (arquivos `geral`/`complemento`/`ativo_passivo`) e devolve `None`, e a resolução de ticker na B3 está quebrada — o `GetListClassFund` passou a exigir `idFNET`, e o cliente envia apenas `idCEM`, recebendo corpo vazio.

## What Changes

- **BREAKING (resolução B3)**: a resolução de ticker passa a usar `GetListFunds` (busca por `acronym` → `id` primário) e a consultar `GetListClassFund` por `idFNET`; corrige a resolução hoje quebrada, pré-requisito de toda a aquisição B3.
- A B3 passa a listar e extrair o **Informe Mensal Estruturado** (`GetStructuredReports`, `type=40`), baixando o documento do FundosNet e extraindo por rótulo: `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`.
- A B3 (type=40) passa a ser a **fonte primária** de cotistas/patrimônio/cotas/VP-Cota, por ser mais atual: disponível por ticker assim que o informe é entregue (ex.: referência 07/2026 entregue em 14/08/2026), contra ~3 semanas de latência do arquivo anual da CVM (revalidado em 05/09/2026).
- A CVM permanece como **fallback**, passando a ler o layout multi-arquivo atual (`inf_mensal_fii_complemento_*`: `Total_Numero_Cotistas`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Valor_Patrimonial_Cotas`), sem abortar a leitura por `CvmSchemaError` de um arquivo isolado.
- As colunas "Nº de cotistas", "Patrimônio" e "VP (VP/Cota)" passam a ser preenchidas a partir da fonte consolidada.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `b3-fii-extraction`: resolução de ticker via `GetListFunds` + `GetListClassFund(idFNET)` e aquisição do Informe Mensal Estruturado (`type=40`) com extração de cotistas/patrimônio/cotas/VP-Cota.
- `cvm-monthly-fund-data`: leitura do layout multi-arquivo atual (`complemento`) e normalização de cotistas/patrimônio/cotas como fonte de fallback.
- `fundamental-source-fallback`: prioridade B3 (primário) → CVM (fallback) para cotistas e patrimônio, preservando a origem e a data de referência.

## Impact

- **Código**: `infrastructure/b3/funds_client.py` (`listar_fundos`, resolução), `infrastructure/b3/fund_repository.py`, `infrastructure/b3/reports_repository.py` (`get_monthly_reports`/`extrair_informe`), novo parser de informe mensal, `infrastructure/fii/b3_fundamental_repository.py` (consolidação), `infrastructure/cvm/schema.py` e `repository.py` (aliases e multi-arquivo), `infrastructure/cvm/patrimonio.py`.
- **Dados/fixtures**: nova fixture HTML do informe mensal B3 (anonimizada) e fixtures do dataset CVM no layout `complemento`.
- **Pré-requisito**: a correção de resolução B3 é bloqueante para a extração `type=40`.
- **Specs-base**: arquivar depois das changes pendentes (`fundamentos-table-data`, `fundamentos-table-ux`, `fundamental-dividend-consolidation`).
- **Compatibilidade**: cotistas/patrimônio passam a ser preenchidos; nenhum cálculo existente muda.
