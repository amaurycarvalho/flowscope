## Why

A tabela da sub-aba "Fundamentos" não expõe o dividendo anterior nem o payout (DY/FFOY), posiciona o FFO Trend de forma pouco informativa e omite preço e VP/Cota, dificultando a leitura conjunta de renda e valuation. Além disso, o sub-tipo concatena suas partes com `"; "`, o que polui a coluna.

## What Changes

- **BREAKING (colunas)**: a tabela fundamentalista passa a exibir, nesta ordem: Ticker, Nome, Tipo, Sub-tipo, Última data-com, Último dividendo, Dividendo anterior, Tendência do dividendo, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), FFO Trend, P (Cotação), VP (VP/Cota), P/FFO, P/VP, Nº de cotistas, Classe de cotistas, Patrimônio, Classe de patrimônio, Data de referência.
- Novas colunas:
  - **Dividendo anterior**: valor do dividendo imediatamente anterior (`UltimoDividendo.valor_anterior`).
  - **Dividend Payout (DY/FFOY)**: razão `Dividend Yield / FFO Yield`.
  - **P (Cotação)**: preço de mercado do ativo (campo `cotacao` do Fundamentus).
  - **VP (VP/Cota)**: valor patrimonial por cota reportado pelo Fundamentus.
- "FFO Trend" é movida para logo após "Dividend Payout (DY/FFOY)".
- Alinhamento à direita do conteúdo das colunas: Último dividendo, Dividendo anterior, FFO Yield, Dividend Yield, Dividend Payout (DY/FFOY), P, VP, P/FFO, P/VP, Nº de cotistas e Patrimônio.
- O sub-tipo passa a concatenar suas partes com `", "` em vez de `"; "` (tanto para FII quanto para Papel).
- O Fundamentus passa a expor `VP/Cota` como campo normalizado da análise fundamentalista.
- **Fora de escopo**: congelamento das colunas Ticker/Nome (não será implementado).

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `gui-interface`: ordem, novas colunas (Dividendo anterior, Dividend Payout, P, VP) e alinhamento à direita das colunas numéricas da tabela fundamentalista.
- `fii-classification`: o separador de concatenação do sub-tipo exibido passa de `"; "` para `", "`.
- `fundamentus-fundamental-provider`: o campo `VP/Cota` passa a ser exposto na composição de campos fundamentalistas.
- `fii-fundamental-metrics`: nova métrica `Dividend Payout` definida como `Dividend Yield / FFO Yield`.

## Impact

- **Código**: `presentation/gui/charts/fundamental_table.py` (colunas, alinhamento e montagem das linhas), `domain/fii/classification.py` (`_juntar`), `domain/fii/analysis.py` (`cotacao` e `vp_cota` no resultado), `application/fundamental_analysis.py` (preenchimento dos novos campos), `application/fundamental_ports.py` (nova chave `CAMPO_VP_COTA`), `infrastructure/fii/fundamentus/adapter.py` (mapeamento de `VP/Cota`).
- **Dados/fixtures**: fixtures do Fundamentus já contêm `Cotação` e `VP/Cota`; o teste de contrato do parser passa a validar o mapeamento.
- **Apresentação**: nenhuma mudança de cálculo de dividendo; `valor_anterior` já é calculado.
- **Compatibilidade**: mudança observável na ordem das colunas, nos rótulos do sub-tipo e no alinhamento; sem congelamento de colunas.
