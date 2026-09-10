## Context

Ver `proposal.md` — Why. O estado atual relevante:

- `AnaliseFundamental` (`domain/fii/analysis.py`) já carrega `ultimo_dividendo: UltimoDividendo`, cujo `valor_anterior` é calculado em `dividends.py`, mas não é exibido.
- `MetricasFii` já carrega `dividend_yield`, `ffo_yield`, `p_ffo`, `p_vp` e `ffo_payout` (que é `dividends_12m / ffo_12m`, numericamente igual a `DY / FFOY`).
- O port `FundamentalDataProvider` já define `CAMPO_COTACAO` e o adapter do Fundamentus mapeia `ativo.cotacao`; porém a análise não propaga `cotacao` para `AnaliseFundamental`.
- O parser do Fundamentus já extrai `VP/Cota` em `AtivoFundamental.indicadores`, mas não há chave de campo nem mapeamento no adapter.
- As colunas da tabela estão em `_COLUNAS` (`presentation/gui/charts/fundamental_table.py`) e a montagem das linhas em `_linha_analise`/`_linha_sintetica`.
- O separador do sub-tipo está em `_juntar` (`domain/fii/classification.py`), hoje `"; "`.

## Goals / Non-Goals

**Goals:**
- Exibir as quatro novas colunas e reordenar FFO Trend, P e VP.
- Alinhar à direita as 11 colunas numéricas listadas.
- Trocar o separador do sub-tipo para `", "`.
- Expor `cotacao` e `vp_cota` como campos normalizados, preenchidos quando a fonte fornecer.

**Non-Goals:**
- Congelar as colunas Ticker/Nome.
- Alterar o cálculo de dividendos, FFO ou patrimônio.
- Introduzir dependências de UI de terceiros.

## Decisions

### 1. `cotacao` e `vp_cota` como campos explícitos de `AnaliseFundamental`
Adicionar `cotacao: Decimal | None` e `vp_cota: Decimal | None` ao resultado da análise e preenchê-los a partir dos campos compostos (`CAMPO_COTACAO`, novo `CAMPO_VP_COTA`).

- **Alternativa descartada**: derivar `cotacao` de `metricas.market_value / shares_outstanding` e `vp_cota` de `cotacao / p_vp`. Falha quando o caminho do motor de FFO não roda (ex.: ativo só com dados do Fundamentus), deixando as colunas `N/A` mesmo com o dado disponível na fonte.
- **Motivo**: o Fundamentus fornece ambos diretamente; exibir o valor reportado é mais fiel.

### 2. Payout calculado na apresentação
Calcular `Dividend Payout (DY/FFOY)` como `dividend_yield / ffo_yield` no momento de montar a linha.

- **Alternativa descartada**: reutilizar `MetricasFii.ffo_payout`. Apesar de ser algebricamente igual (`dividends_12m / ffo_12m`), `ffo_payout` só é populado pelo motor FFO (`analisar_snapshot`), ficando `None` no caminho de campos reportados pelo Fundamentus.
- **Nota**: a métrica `Dividend Payout` é especificada em `fii-fundamental-metrics`; a apresentação apenas a materializa.

### 3. Novo campo `CAMPO_VP_COTA`
Adicionar a chave `vp_cota` em `fundamental_ports.py`, incluí-la em `CAMPOS_FUNDAMENTAIS` e mapear o indicador `VP/Cota` no adapter do Fundamentus.

- **Alternativa descartada**: derivar `vp_cota = cotacao / p_vp`. Menos fiel e sujeito a inconsistência de arredondamento do `P/VP` reportado.

### 4. Alinhamento por coluna via `anchor`
Aplicar `tree.column(coluna_id, anchor="e")` nas 11 colunas numéricas no `FundamentalTablePanel`.

### 5. Separador `", "`
Alterar `_juntar` em `classification.py` para `", "`, afetando igualmente FII e Papel.

## Risks / Trade-offs

- **[Specs-base dessincronizadas]** As changes `fundamentos-table-data`, `fundamentos-table-ux` e `fundamental-dividend-consolidation` estão completas mas não arquivadas, e os deltas deste change foram escritos sobre o estado pós-arquivamento delas. → **Mitigação**: arquivar as changes pendentes antes de arquivar esta; registrar a ordem no proposal/tasks.
- **[Testes posicionais]** `tests/test_presentation/test_fundamental_table.py` referencia índices de coluna (`colunas[7]`, etc.) e o cabeçalho do CSV. → **Mitigação**: atualizar os índices e o cabeçalho esperado junto com a mudança.
- **[Divergência `P/VP` × `VP/Cota`]** Valores reportados separadamente pelo Fundamentus podem diferir por arredondamento. → **Mitigação**: exibir cada um como reportado; não reconciliar na apresentação.
- **[Rótulo da coluna de cotistas]** O texto atual é `Nº de cotistas`; o pedido menciona "Número de cotistas". → Decisão de manter o rótulo atual para minimizar churn; ajustável sem impacto de dados.
