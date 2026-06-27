## Why

Dois pequenos atritos no uso diário: clicar "Hoje" não carrega dados automaticamente (obriga um clique extra em "Carregar"), e os diálogos de salvar/carregar tickers sempre abrem na pasta padrão do sistema em vez da última pasta usada.

## What Changes

- Botão "Hoje" agora também executa `_on_load_data` após atualizar a data
- `TickerList._save()` e `TickerList._load()` passam a usar `initialdir` a partir de uma preferência persistida
- A preferência `last_ticker_dir` é adicionada ao `~/.flowscope/config.json` e salva sempre que o usuário seleciona uma pasta nos diálogos de ticker
- `TickerList` recebe parâmetros `initialdir` e `on_dir_changed` callback (baixo acoplamento)

## Capabilities

### New Capabilities
Nenhuma — ambas as mudanças são modificações em capacidades existentes.

### Modified Capabilities
- `gui-interface`: Comportamento do botão "Hoje" passa a incluir carregamento automático de dados
- `ui-polish`: Preferências persistentes agora incluem `last_ticker_dir`

## Impact

- **Target**: Release 0.1.0
- `src/flowscope/presentation/gui/app.py`: `_on_today()` chamará `_on_load_data()`; config incluirá `last_ticker_dir`; `TickerList` receberá `initialdir` e `on_dir_changed`
- `src/flowscope/presentation/gui/widgets/ticker_list.py`: `_save()` e `_load()` usarão `initialdir` e dispararão `on_dir_changed`
- Nenhuma nova dependência externa
- Nenhuma mudança em APIs ou schemas de dados
