## Why

Atualmente o carregamento de dados mostra apenas um texto animado ("Carregando...") sem informar o progresso real. O usuário não sabe se o sistema está no dia 1 de 7, se travou, ou quanto tempo falta. Isso é frustrante em operações que podem levar vários segundos (download de 7 datas + processamento de centenas de tickers).

## What Changes

- Substituir o texto animado atual por uma **barra de progresso determinate** (`ttk.Progressbar`) na statusbar
- A barra é acompanhada por um **rótulo textual** lado a lado descrevendo a etapa atual
- O progresso é informado em **múltiplas fases**: download de datas, processamento de indicadores, carregamento de portfólio
- Cada data baixada/processada incrementa o progresso; falhas são contabilizadas separadamente
- Dados em cache (já baixados) são pulados com progresso refletido ("100% — Em cache")
- Portfolio loading mostra texto informativo "Baixando portfólio IBOV..." sem barra dedicada, mas como passo da progressão geral
- Injetar um **callback de progresso** nas camadas de application/infrastructure para reportar o andamento

## Capabilities

### New Capabilities
- `progress-indicator`: Barra de progresso determinate na statusbar com label descritivo, reportando o andamento do carregamento de dados externos (B3) e processamento de indicadores

### Modified Capabilities

*(Nenhuma — as capacidades existentes de ingestão de dados e GUI não têm seus requisitos alterados, apenas a experiência de carregamento é melhorada)*

## Impact

- `src/flowscope/presentation/gui/app.py` — Statusbar: de `tk.Label` para `tk.Frame` com `ttk.Progressbar` + `tk.Label`. Métodos `_enter_loading_state`/`_exit_loading_state`/`_animate_loading` substituídos por um sistema de progresso com etapas.
- `src/flowscope/application/use_cases.py` — `AnalyzeTickersUseCase.execute()` recebe `progress_callback` opcional.
- `src/flowscope/infrastructure/b3/repository.py` — `fetch_trades()` repassa callback para cada data processada.
- `src/flowscope/infrastructure/b3/client.py` — `fetch_file()` e `fetch_portfolio()` aceitam e invocam callback de progresso.
- `src/flowscope/domain/engine.py` — `IndicatorEngine.execute()` aceita callback para reportar progresso do processamento de indicadores.
