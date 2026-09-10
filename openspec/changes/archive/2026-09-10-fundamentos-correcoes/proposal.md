## Why

A sub-aba "Fundamentos" exibe dados incompletos ou incorretos. Para FIIs, a extração dos documentos de provento da B3 lê o layout real errado: o tipo vira `Amortização` e a data-base fica vazia, então todo provento B3 é descartado e a coluna cai no valor único do Fundamentus — deixando "Última data-com", "Dividendo anterior" e "Tendência do dividendo" em `N/A`. Para Papel, não existe fonte de histórico de proventos no wiring (o repositório B3 é FII-only) e o `VPA` já disponível no Fundamentus não é mapeado para a coluna VP. Além disso, as colunas numéricas misturam quantidades de casas decimais, dificultando a leitura.

## What Changes

- **Layout**: formatar com exatamente 2 casas decimais as colunas "Último dividendo", "Dividendo anterior", "Dividend Payout (DY/FFOY)", "P (Cotação)" e "VP (VP/Cota)".
- **B3 (FII)**: corrigir o parser do documento FundosNet para o layout real de duas colunas (`Rendimento | Amortização`), identificando o tipo pela coluna que contém o valor e extraindo a `Data-base` do rótulo parentético. Adicionar fixture de contrato do documento real.
- **Fundamentus (Papel)**: expor o indicador `VPA` como `vp_cota` para ações e prover o histórico de proventos de `proventos.php` como uma implementação de `DividendHistoryProvider`.
- **Dividendos**: ligar o `historico_dividendos` no wiring e consolidar B3 (FII) + histórico Fundamentus para preencher data-com, último/anterior e tendência em FII e Papel.
- **BREAKING (dados exibidos)**: para FIIs, "Último dividendo" passa a ser o rendimento mais recente da B3 (com data real) em vez do `Dividendo/cota` do Fundamentus; a formatação fixa de 2 casas altera a saída textual e o CSV.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: as fontes são extensões de providers existentes. -->

### Modified Capabilities
- `gui-interface`: formatação numérica com 2 casas decimais para as colunas de dividendo, payout, P e VP; coluna VP preenchida para Papel a partir do `VPA`.
- `b3-fii-extraction`: extração correta de tipo (`Rendimento`/`Amortização`) e `Data-base` do documento FundosNet real, com fixture de contrato.
- `fundamentus-fundamental-provider`: exposição de `VPA` para ações como `vp_cota` e de histórico de proventos (`proventos.php`) como fonte de dividendos.
- `dividend-metrics`: consolidação de histórico para Papel e FII com a fonte secundária de proventos, preenchendo data-com, dividendo anterior e tendência.

## Impact

- **Código**: `infrastructure/b3/structured_extractor.py`, `infrastructure/b3/structured_parser.py`; `infrastructure/fii/fundamentus/` (parser, client, adapter, provider); `application/fundamental_analysis.py`; `presentation/gui/charts/fundamental_table.py`; `presentation/gui/controller.py` e `app.py`.
- **APIs**: `fnet.bmfbovespa.com.br` (documento de provento) e `fundamentus.com.br/proventos.php` (histórico). Nenhuma credencial.
- **Cache**: nova chave de cache por ticker para o histórico de proventos do Fundamentus.
- **Testes**: fixtures de contrato do documento B3 real e da página `proventos.php`; atualização dos testes de formatação da tabela.
- **Compatibilidade**: linhas sintéticas e tickers sem dado permanecem `N/A`; nenhum contrato de porta é removido (apenas passa a ser usado `historico_dividendos`).
