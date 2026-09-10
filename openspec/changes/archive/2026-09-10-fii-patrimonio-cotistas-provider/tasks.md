## 1. Resolução de ticker na B3

- [x] 1.1 Adicionar `listar_fundos()` ao `B3FundosClient` consultando `GetListFunds` de forma paginada e cacheada; verificar com teste que múltiplas páginas são consolidadas
- [x] 1.2 Reescrever `selecionar_candidato`/`resolver_ticker` para o fluxo `GetListFunds` (acronym → id primário) → `GetListClassFund(idFNET)` → registro com `idMain`; verificar com teste sobre a fixture `tests/fixtures/b3/fund_alzr.json` e a lista de fundos que o `idFNET` resolvido é `20294`
- [x] 1.3 Deixar de cachear `None` na resolução (ou usar TTL curto) para não congelar falha transitória; verificar com teste de duas chamadas após falha seguida de sucesso

## 2. Aquisição do Informe Mensal Estruturado (type=40)

- [x] 2.1 Adicionar `TIPO_INFORME_MENSAL = 40` e `get_monthly_reports` ao `B3ReportsRepository`; verificar com fixture do índice `type=40` que os documentos ativos são listados
- [x] 2.2 Implementar o parser do informe mensal (rótulo → próxima célula, com normalização de acentos/`¹`) extraindo `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`; verificar com fixture HTML real anonimizada do informe
- [x] 2.3 Selecionar o informe ativo mais recente com referência ≤ data de referência e distinguir ausência de falha de download; verificar com testes de lista vazia e de falha de rede

## 3. Consolidação B3 → CVM

- [x] 3.1 Implementar a fonte de patrimônio B3 a partir do informe (net asset value, cotas, cotistas, VP/Cota) e consolidar em `B3FundamentalRepository.obter_patrimonio` com B3 primário e CVM fallback, preservando `fonte` e `reference_date`; verificar com testes de B3 presente, B3 ausente/CVM presente e ambos ausentes

## 4. Correção do fallback CVM

- [x] 4.1 Atualizar os aliases do schema (`Patrimonio_Liquido`, `Cotas_Emitidas`, `Total_Numero_Cotistas`, `Valor_Patrimonial_Cotas`) e fazer `_ler_linhas` ignorar CSVs sem as colunas obrigatórias em vez de abortar; verificar com CSV no layout `complemento` real
- [x] 4.2 Garantir que `CvmMonthlyPatrimonioSource.patrimonio` retorna cotistas/patrimônio a partir do `complemento`; verificar com teste ponta-a-ponta usando o ZIP fixture

## 5. Verificação final

- [x] 5.1 Rodar `ruff check` e a suíte de testes afetada; verificar que não há regressões
