## Why

A tendência do dividendo hoje usa uma banda de tolerância de ±5% e rótulos (`SUBINDO`/`CAINDO`/`MANTEVE`) que não refletem a leitura pedida pelo usuário (comparação direta igual/acima/abaixo). Além disso, a última data-com e o dividendo anterior vêm apenas do histórico B3, deixando a coluna vazia quando a B3 não cobre o ativo.

## What Changes

- **BREAKING (rótulos)**: a tendência do dividendo passa a ser `Neutro` (igual), `Crescimento` (acima) e `Redução` (abaixo), por comparação direta entre o último dividendo e o anterior, sem banda de tolerância.
- A última data-com e o par último/anterior de dividendos passam a ser consolidados a partir do histórico B3 (primário), CVM (secundário) e Fundamentus (fallback), preenchendo o que estiver faltando.
- A coluna "Última data-com" da tabela passa a ser preenchida para todos os tickers em que houver dado consolidado.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `dividend-metrics`: a regra de tendência passa a ser igual/acima/abaixo com rótulos `Neutro`/`Crescimento`/`Redução`; a banda de ±5% é removida; a última data-com e o dividendo anterior passam a ser consolidados de B3, CVM e Fundamentus.

## Impact

- **Código**: `domain/fii/dividends.py` (enum `TendenciaDividendo`, `calcular_tendencia`, `calcular_ultimo_dividendo`), `application/fundamental_analysis.py`, `infrastructure/fii/b3_fundamental_repository.py` (consolidação de fontes).
- **Apresentação**: `charts/fundamental_table.py` passa a exibir os novos rótulos.
- **Specs-base**: arquivar **depois** de `fundamental-metrics-table` (materializa `dividend-metrics`).
- **Compatibilidade**: mudança observável nos valores da coluna "Tendência do dividendo".
