## Why

FlowScope é um projeto greenfield — não há código-fonte, estrutura de projeto ou implementação alguma. Esta change estabelece toda a fundação do projeto: estrutura de diretórios conforme Clean Architecture, camada de domínio com indicadores de fluxo de ordens (CVD, VWAP, Volume Profile), ingestão de dados da B3 via API com janela temporal de Fibonacci, interfaces CLI e GUI, exportação para clipboard, empacotamento com PyInstaller e suporte a atalho desktop no Linux. Sem esta change, o projeto não existe como software funcional.

## What Changes

- **Estrutura de projeto**: Criação de diretórios `src/flowscope/` e `tests/` com `pyproject.toml`, seguindo Clean Architecture tradicional (domain, application, infrastructure, presentation)
- **Ícones**: Movidos de `icons/` para `src/flowscope/icons/`
- **Ingestão de dados**: Cliente HTTP para API B3 (two-step: requestname → token → download), parser de CSV consolidado, seleção de datas via janela Fibonacci (d-1, d-2, d-3, d-5, d-8, d-13, d-21) com ajuste para dias úteis
- **Indicadores**: Cálculo de Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile a partir dos dados consolidados
- **CLI**: argparse com flags `--gui`, `--tickers`, `--vwap`, `--cvd`, `--help`, `--version`, `--create-shortcut`
- **GUI**: Interface Tkinter com tkcalendar (seleção de data), matplotlib (histogramas VWAP/CVD, scatter plot VWAP×CVD com quiver opcional), campo de seleção/edição de tickers com load/save `.txt`, campo readonly para análise automática (placeholder), botões de clipboard
- **Clipboard**: Exportação CSV (texto) via pyxclip; exportação de gráfico (imagem) via ctypes + comandos nativos por plataforma
- **Atalho desktop**: `--create-shortcut` gera `.desktop` file no Linux
- **Empacotamento**: Atualização de `flowscope.spec` (PyInstaller) e `Makefile` para refletir a nova estrutura
- **Testes**: Estrutura de testes em `tests/` com unittest/pytest

## Capabilities

### New Capabilities

- `project-scaffold`: Estrutura de diretórios Clean Architecture, pyproject.toml, reorganização de recursos estáticos (ícones) para dentro do pacote, scripts de build e empacotamento (Makefile, PyInstaller .spec)
- `data-ingestion`: Download de arquivos consolidados da B3 via API two-step, parsing de CSV com schema TradeInformationConsolidated, seleção de janela temporal com offsets de Fibonacci e ajuste para dias úteis, cache local dos arquivos baixados
- `volume-indicators`: Cálculo de Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile a partir dos dados consolidados por ticker, seleção automática dos 15 tickers com maior volume financeiro no período
- `cli-interface`: Ponto de entrada via linha de comando com argparse, suporte a todos os flags (`--gui`, `--tickers`, `--vwap`, `--cvd`, `--help`, `--version`, `--create-shortcut`), exportação CSV dos indicadores
- `gui-interface`: Interface gráfica Tkinter com tkcalendar para seleção de data, gráficos matplotlib (histogramas VWAP/CVD por ticker, scatter plot VWAP×CVD com quiver temporal), campo multilinha de seleção de tickers com load/save .txt, campo readonly para análise automática (placeholder para motor de inferência futuro)
- `clipboard-export`: Cópia de dados CSV para clipboard (pyxclip) e cópia de gráfico como imagem PNG para clipboard (ctypes + comandos nativos: xclip no Linux, win32clipboard no Windows, osascript no macOS)
- `desktop-shortcut`: Criação de atalho `.desktop` no Linux via flag `--create-shortcut`

### Modified Capabilities

<!-- Nenhuma — projeto greenfield, não há capabilities existentes. -->

## Impact

- **Código novo**: Todo o código-fonte em `src/flowscope/` (domain, application, infrastructure, presentation)
- **Dependências**: matplotlib, Pillow, tkinter, tkcalendar, pyxclip, ctypes (stdlib), pytest (dev)
- **Build**: Atualização de `flowscope.spec` e `Makefile` para apontar para nova estrutura; `pyproject.toml` como configuração central do projeto
- **README.md**: Atualização dos comandos de uso para refletir `python3 -m flowscope` ao invés de `python3 flowscope.py`
- **CI/CD**: `.github/workflows/` precisará de workflow de build/test (a ser tratado em change separada ou como parte desta se houver tasks)
