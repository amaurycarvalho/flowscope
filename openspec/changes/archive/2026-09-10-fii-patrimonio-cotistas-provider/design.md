## Context

Ver `proposal.md` — Why. O estado atual relevante e as evidências levantadas:

- **Resolução B3 quebrada**: `B3FundosClient.listar_candidatos` envia `{"idCEM": ticker}` sem `idFNET`. A B3 responde `200` com corpo vazio (o `idCEM` é ignorado) e o cliente devolve `[]`. Verificado: `GetListFunds` lista 528 fundos (`acronym`, `id`); `GetListClassFund` só responde com `idFNET` do `id` primário (ex.: ALZR → 870 → classes com `id=20294, idMain=870`).
- **Informe type=40**: `GetStructuredReports` com `dataInicial`/`dataFinal` e `type=40` retorna o índice; o documento do FundosNet (`exibirDocumento?id=`) é HTML com linhas `rótulo → valor`. Campos verificados no informe ALZR 07/2026: `Número de cotistas=206.111`, `Patrimônio Líquido – R$=1.773.014.664,80`, `Número de Cotas Emitidas=164.444.501,0000`, `Valor Patrimonial das Cotas – R$=10,781842`.
- **CVM layout atual**: `inf_mensal_fii_<ano>.zip` contém `geral`, `complemento` e `ativo_passivo`. Cotistas e patrimônio estão no `complemento`: `Total_Numero_Cotistas`, `Patrimonio_Liquido`, `Cotas_Emitidas`, `Valor_Patrimonial_Cotas`. O adapter atual espera `VL_PATRIM_LIQ`/`QT_COTA`/`NR_COTST` e um único CSV, lança `CvmSchemaError` e devolve `None` (a exceção é engolida em `CvmMonthlyPatrimonioSource`).
- **Atualidade**: o informe B3 é entregue por ticker (ex.: 14/08/2026) e fica disponível de imediato; o ZIP anual da CVM foi revalidado em 05/09/2026 — ~3 semanas depois. Os valores são idênticos para a mesma competência.

## Goals / Non-Goals

**Goals:**
- Restaurar a resolução de ticker B3 e habilitar a aquisição `type=40`.
- Preencher cotistas/patrimônio/cotas/VP-Cota com B3 primário e CVM fallback.
- Ler o layout multi-arquivo atual da CVM sem abortar a consulta.

**Non-Goals:**
- Alterar os cálculos de métricas ou a apresentação da tabela.
- Tratar PDFs ou outros formatos de informe.
- Mudar o layout das colunas (change `fundamentos-table-columns`).

## Decisions

### 1. Resolução em duas etapas com `GetListFunds`
Adicionar `listar_fundos()` a `B3FundosClient` (paginado) e reescrever `selecionar_candidato`/`resolver_ticker` para: localizar `acronym` → `id` primário em `GetListFunds`; consultar `GetListClassFund` com `idFNET`; escolher o registro com `idMain` não nulo.

- **Alternativa descartada**: continuar com `GetListClassFund` por `idCEM` — hoje retorna vazio.
- **Cache**: a lista de fundos é cacheada (30 dias) e a resolução por ticker mantém o cache existente.

### 2. Aquisição `type=40` e parser por rótulo
Adicionar `TIPO_INFORME_MENSAL = 40` e `get_monthly_reports`/`extrair_informe_mensal` em `B3ReportsRepository`, baixando apenas o documento ativo mais recente ≤ data de referência. O parser reutiliza a estratégia rótulo→próxima célula, normalizando acentos e o sobrescrito `¹` dos rótulos.

- **Alternativa descartada**: reutilizar o parser de proventos (`type=41`), que busca ISIN e campos de provento, ausentes no informe.

### 3. Consolidação B3 → CVM
`B3FundamentalRepository.obter_patrimonio` passa a consultar primeiro a fonte B3 (`type=40`) e, se ausente, a CVM; retorna `PatrimonioFii` com `fonte` e `reference_date` da origem usada.

- **Alternativa descartada**: manter apenas a CVM — mais defasada e hoje quebrada.
- **Nota**: `VP/Cota` é derivável de `net_asset_value / shares_outstanding`, mas o informe o reporta diretamente; o valor reportado é preferido.

### 4. CVM multi-arquivo com skip por arquivo
Adicionar os aliases atuais (`Patrimonio_Liquido`, `Cotas_Emitidas`, `Total_Numero_Cotistas`, `Valor_Patrimonial_Cotas`) e fazer `_ler_linhas` ignorar CSVs sem as colunas obrigatórias, em vez de propagar `CvmSchemaError` que aborta toda a consulta.

- **Alternativa descartada**: manter o erro por arquivo — hoje inutiliza o fallback.

## Risks / Trade-offs

- **[Paginação do `GetListFunds`]** `pageSize=1000` retorna vazio; é preciso paginar. → **Mitigação**: paginar com o tamanho que funciona (20) e cachear a lista; cobrir com teste de múltiplas páginas.
- **[Cache de falha de resolução]** `resolver_ticker` cacheia `None` por 30 dias, podendo congelar uma falha transitória. → **Mitigação**: não cachear `None` (ou usar TTL curto) e cobrir com teste.
- **[Variantes de rótulo do informe]** Acentuação e sobrescrito variam entre fundos. → **Mitigação**: normalizar rótulos (sem acento/`¹`) e testar com fixture real anonimizada.
- **[Mudança futura do layout CVM]** O dataset já mudou uma vez. → **Mitigação**: manter o versionamento de schema e testes de contrato com o layout `complemento`.
- **[Specs-base dessincronizadas]** Arquivar depois das changes pendentes.
