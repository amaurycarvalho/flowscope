## Why

Os campos de *short interest* (`Shorts%`, `Volume de Shorts`, `Fechamento Shorts`, `Risco Fechamento`) aparecem como `N/A`/`Inexistente` em datas recentes mesmo quando a B3 já publicou as Posições em Aberto. O `B3ShortInterestSource` gravava um mapa vazio quando o dia era consultado antes da publicação e nunca o revia, prendendo o ticker em `N/A`; o recuo de 7 dias não recuperava o dia envenenado.

## What Changes

- O cache de ações alugadas passa a **não persistir mapa vazio**: um dia consultado antes da publicação é reconsultado em execuções seguintes.
- Um cache vazio já gravado passa a ser tratado como ausência (*miss*), forçando a recoleta do dia.
- O construtor do `B3ShortInterestSource` passa a **descartar caches vazios legados** (`b3_emprestimos_btb-v1_*.json` com `data` vazio), análogo ao *bust* de portfólio do `B3Client`.
- O comportamento observável dos cálculos (Shorts%, SIR e classificações) permanece inalterado; muda apenas a disponibilidade do insumo ao longo do tempo.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `short-interest`: o requisito de ausência de dados passa a distinguir indisponibilidade definitiva de dados ainda não publicados, exigindo que um cache vazio não seja usado como resultado definitivo nem persistido.

## Impact

- `src/flowscope/infrastructure/b3/emprestimos.py` (`_mapa`, novo `_bust_stale_empty_cache`).
- `tests/test_infrastructure/test_b3_emprestimos.py`.
- Sem mudança em `application`, `domain` ou na apresentação.
