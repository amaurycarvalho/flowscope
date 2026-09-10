## Why

A sub-aba "Fundamentos" não exibe P/L, e a ordem das colunas mistura preço/VP com o bloco de dividendos, dificultando a leitura comparativa. Além disso, "Tendência do dividendo" usa rótulos binários (`Crescimento`/`Redução`) sem bandas de tolerância, e "FFO Trend" exibe os identificadores técnicos do enum (`FORTE_ALTA`) em vez de rótulos descritivos. Para Papel, a coluna "Nº de cotistas" fica sempre `N/A`, embora a CVM publique a quantidade de acionistas no Formulário de Referência (FRE).

## What Changes

- **Layout**: reordenar as colunas da tabela de Fundamentos para `Ticker;Nome;Tipo;Sub-tipo;P (Cotação);VP (VP/Cota);P/VP;P/L;Dividend Yield;Última data-com;Último dividendo;Dividendo anterior;Tendência do dividendo;FFO Yield;Dividend Payout (DY/FFOY);FFO Trend;P/FFO;Nº de cotistas;Classe de cotistas;Patrimônio;Classe de patrimônio;Data de referência`, adicionando a coluna `P/L` após `P/VP` e alinhando-a à direita.
- **P/L (Papel)**: expor o indicador `P/L` do Fundamentus como campo fundamentalista e exibi-lo na tabela.
- **P/L (FII)**: calcular `P/L = Preço / (Último dividendo × 12)`, anualizando o dividendo mensal para expressar a quantidade de anos, por função pura de domínio, com `N/A` quando o último dividendo for ausente ou zero.
- **Nº de acionistas (Papel)**: obter a quantidade de acionistas do FRE (`distribuicao_capital`, somando pessoa física, pessoa jurídica e investidores institucionais) usando a ponte ticker→CNPJ do FCA (`valor_mobiliario`), preenchendo "Nº de cotistas" e reutilizando `classificar_cotistas` para "Classe de cotistas". FII mantém a fonte atual (Informe Mensal/B3).
- **Rótulos de tendência**: exibir rótulos descritivos no lugar dos identificadores do enum: `FORTE_ALTA` = `Forte Alta`, `ALTA` = `Leve Alta`, `ESTAVEL` = `Estável`, `QUEDA` = `Leve Queda` e `FORTE_QUEDA` = `Forte Queda`.
- **Tendência do dividendo**: classificar em cinco faixas percentuais com os mesmos rótulos do FFO Trend: `Forte Alta` (≥ +5%), `Leve Alta` (> 0% e < +5%), `Estável` (= 0%), `Leve Queda` (≥ −5% e < 0%) e `Forte Queda` (< −5%).
- **BREAKING (valores exibidos)**: os valores de `TendenciaDividendo` deixam de ser `Crescimento`/`Redução`/`Neutro` e passam às faixas do FFO Trend, alterando a saída textual/CSV e os testes de tendência; "FFO Trend" deixa de exibir `FORTE_ALTA` e passa a exibir `Forte Alta`.

## Capabilities

### New Capabilities
- `cvm-fre-acionistas`: aquisição e resolução da quantidade de acionistas de companhias abertas (Papel) a partir do FRE (`distribuicao_capital`), com ponte ticker→CNPJ pelo FCA (`valor_mobiliario`).

### Modified Capabilities
- `gui-interface`: ordem das colunas, coluna `P/L` e rótulos descritivos de tendência (FFO e dividendo).
- `fundamentus-fundamental-provider`: exposição do indicador `P/L` como campo fundamentalista.
- `fii-fundamental-metrics`: P/L derivado para FII e preenchimento de cotistas/acionistas para Papel com classificação reutilizada.
- `dividend-metrics`: classificação da tendência do dividendo em faixas percentuais.

## Impact

- **Código**: `presentation/gui/charts/fundamental_table.py`; `application/fundamental_ports.py` e `application/fundamental_analysis.py`; `domain/fii/analysis.py`, `domain/fii/dividends.py` e `domain/fii/metrics.py`; `infrastructure/fii/fundamentus/adapter.py`; novo fluxo em `infrastructure/cvm/` (FRE + FCA).
- **APIs**: dados abertos da CVM — `FRE` (`fre_cia_aberta_distribuicao_capital_YYYY.zip`) e `FCA` (`fca_cia_aberta_valor_mobiliario_YYYY.zip`). Nenhuma credencial.
- **Cache**: novas chaves anuais para os arquivos brutos do FRE e do FCA; cache das informações normalizadas (mapa ticker→CNPJ e quantidade por CNPJ) associado ao hash do arquivo e à versão do parser; cache do Fundamentus versionado por parser.
- **Testes**: fixtures FRE/FCA; atualização dos testes de ordem/índices da tabela, de `TendenciaDividendo` e dos rótulos de tendência.
- **Compatibilidade**: linhas sintéticas e dados ausentes permanecem `N/A`; nenhum contrato de porta é removido.
