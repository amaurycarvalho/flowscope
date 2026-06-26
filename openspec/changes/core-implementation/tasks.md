## 1. Estrutura do Projeto

- [ ] 1.1 Criar diretórios Clean Architecture: `src/flowscope/{domain,application,infrastructure,infrastructure/b3,presentation,presentation/gui,presentation/gui/widgets,presentation/gui/charts,icons}` com `__init__.py` em cada
- [ ] 1.2 Criar diretório `tests/` com `__init__.py`
- [ ] 1.3 Criar `pyproject.toml` com metadados, entry point `flowscope = "flowscope.presentation.main:main"`, dependências (`matplotlib`, `Pillow`, `pyxclip`, `tkcalendar`) e dependências dev (`pytest`)
- [ ] 1.4 Mover arquivos de `icons/` para `src/flowscope/icons/` e remover diretório `icons/` original
- [ ] 1.5 Atualizar `Makefile` para usar `python3 -m flowscope`, apontar PyInstaller para entry point correto, e usar `pytest` ou `unittest discover -s tests`
- [ ] 1.6 Atualizar `flowscope.spec` para `Analysis(['src/flowscope/presentation/main.py'],` e `datas=[('src/flowscope/icons/flowscope.png', 'icons')]`
- [ ] 1.7 Atualizar `README.md` trocando `python3 flowscope.py` por `python3 -m flowscope` (ou `flowscope`) em todos os exemplos e seções
- [ ] 1.8 Criar `requirements.txt` (se ainda usado) sincronizado com `pyproject.toml`

## 2. Domínio — Entidades e Value Objects

- [ ] 2.1 Criar `domain/value_objects.py`: `Price` (Decimal), `Volume` (int), `Delta` (float), `Ticker` (str validado)
- [ ] 2.2 Criar `domain/entities.py`: `TradeDay` (data, ticker, min_price, max_price, avg_price, last_price, trades_qty, fin_vol, fin_instr_qty)
- [ ] 2.3 Criar `domain/entities.py`: `AggregatedMetrics` (ticker, cvd, vwap, volume_profile, daily_breakdown dict por data)

## 3. Domínio — Indicadores

- [ ] 3.1 Implementar `domain/indicators.py`: função `calculate_vwap(trades: list[TradeDay]) -> dict` que calcula VWAP diário e consolidado por ticker
- [ ] 3.2 Implementar `domain/indicators.py`: função `calculate_cvd(trades: list[TradeDay]) -> dict` que calcula CVD acumulado e diário por ticker
- [ ] 3.3 Implementar `domain/indicators.py`: função `calculate_volume_profile(trades: list[TradeDay], tick_size: float) -> dict` que distribui volume financeiro em buckets de preço
- [ ] 3.4 Implementar `domain/indicators.py`: função `select_top_tickers(trades: list[TradeDay], n: int = 15) -> list[str]` que retorna os N tickers com maior NtlFinVol agregado

## 4. Aplicação — Casos de Uso e Portas

- [ ] 4.1 Criar `application/ports.py`: interface `DataRepository` (protocolo) com métodos `fetch_trades(date_range, tickers)` e `get_available_dates(ref_date)`
- [ ] 4.2 Criar `application/use_cases.py`: `AnalyzeTickersUseCase` que orquestra fetch → indicadores → resultado
- [ ] 4.3 Criar `application/use_cases.py`: `ExportVWAPUseCase` e `ExportCVDUseCase` que geram CSV a partir dos indicadores

## 5. Infraestrutura — B3 Client e Parser

- [ ] 5.1 Implementar `infrastructure/b3/calendar.py`: função `fibonacci_dates(ref_date: date) -> list[date]` que calcula offsets (1,2,3,5,8,13,21) com ajuste para próximo dia útil (aproximação local, não em cadeia)
- [ ] 5.2 Implementar `infrastructure/b3/client.py`: classe `B3Client` com método `_request_token(file_name, date) -> dict` que faz POST para `api/download/requestname` e retorna token + redirectUrl
- [ ] 5.3 Implementar `infrastructure/b3/client.py`: método `_download_csv(token) -> str` que faz GET para `api/download/?token=` e retorna conteúdo CSV como string
- [ ] 5.4 Implementar `infrastructure/b3/client.py`: método `fetch_file(date) -> str` que orquestra two-step (token → download), usando cache se disponível
- [ ] 5.5 Implementar `infrastructure/b3/parser.py`: função `parse_csv(content: str) -> list[TradeDay]` usando `csv.DictReader` com delimitador `;`, tratamento de campos vazios e conversão de tipos
- [ ] 5.6 Implementar `infrastructure/cache.py`: classe `CacheManager` com métodos `get(date)`, `put(date, content)`, `get_cache_dir()`, determinando diretório por plataforma

## 6. Infraestrutura — Repositório Concreto

- [ ] 6.1 Implementar classe `B3DataRepository` que implementa `DataRepository`, usando `B3Client` + `fibonacci_dates` + `parse_csv` + `CacheManager`
- [ ] 6.2 Adicionar tratamento de erros: API indisponível, token inválido, CSV mal formatado — com mensagens em português

## 7. CLI — Interface de Linha de Comando

- [ ] 7.1 Implementar `presentation/cli.py`: configurar `argparse.ArgumentParser` com todos os flags (`--gui`, `--tickers`, `--vwap`, `--cvd`, `--help`, `--version`, `--create-shortcut`)
- [ ] 7.2 Implementar `presentation/cli.py`: função `run_cli(args)` que executa fluxo padrão (download dados, calcular indicadores, exibir resumo no terminal) quando nenhum flag especial é usado
- [ ] 7.3 Implementar `presentation/cli.py`: função `export_vwap_csv(tickers, metrics, output_path)` que gera CSV com colunas Ticker, VWAP_Periodo e VWAPs diários
- [ ] 7.4 Implementar `presentation/cli.py`: função `export_cvd_csv(tickers, metrics, output_path)` que gera CSV com colunas Ticker, CVD_Acumulado e CVDs diários

## 8. Entry Point

- [ ] 8.1 Implementar `presentation/main.py`: função `main()` que faz parse dos args, carrega tickers do arquivo se `--tickers`, e faz dispatch: `--gui` → abre GUI, `--help` → mostra help, `--version` → mostra versão, `--vwap`/`--cvd` → exporta, `--create-shortcut` → cria atalho, default → CLI

## 9. GUI — Janela Principal

- [ ] 9.1 Implementar `presentation/gui/app.py`: classe `FlowScopeGUI` (herda `tk.Tk` ou compõe) com título "FlowScope", dimensão mínima 1024x768, layout com grid de widgets e gráficos
- [ ] 9.2 Implementar `presentation/gui/app.py`: barra superior com tkcalendar.DateEntry para data de referência + label
- [ ] 9.3 Implementar callback de mudança de data: recalcular janela Fibonacci, refazer fetch se necessário, atualizar todos os gráficos

## 10. GUI — Widgets

- [ ] 10.1 Implementar `presentation/gui/widgets/ticker_list.py`: campo `tk.Text` multilinha, preenchido com top 15 tickers, um por linha
- [ ] 10.2 Implementar `presentation/gui/widgets/ticker_list.py`: botão "Salvar Tickers" que abre `filedialog.asksaveasfilename` e salva conteúdo do campo como `.txt`
- [ ] 10.3 Implementar `presentation/gui/widgets/ticker_list.py`: botão "Carregar Tickers" que abre `filedialog.askopenfilename` e carrega `.txt` no campo
- [ ] 10.4 Implementar `presentation/gui/widgets/analysis_text.py`: campo `tk.Text` readonly com mensagem placeholder "Análise automática será implementada em versão futura."

## 11. GUI — Gráficos Matplotlib

- [ ] 11.1 Implementar `presentation/gui/charts/vwap_hist.py`: gerar `matplotlib.figure.Figure` com gráfico de barras do VWAP por ticker, embutir via `FigureCanvasTkAgg` em frame Tkinter
- [ ] 11.2 Implementar `presentation/gui/charts/cvd_hist.py`: gerar `matplotlib.figure.Figure` com gráfico de barras do CVD por ticker, cores verde (positivo) e vermelho (negativo), embutir via `FigureCanvasTkAgg`
- [ ] 11.3 Implementar `presentation/gui/charts/scatter.py`: gerar scatter plot VWAP (X) × CVD (Y), tamanho do marcador proporcional a NtlFinVol, cor por quadrante
- [ ] 11.4 Implementar `presentation/gui/charts/scatter.py`: checkbox "Exibir setas temporais" que adiciona/remove setas quiver conectando posição de cada ticker em d-1 → d
- [ ] 11.5 Adicionar labels de ticker nos pontos do scatter plot (anotações matplotlib)

## 12. GUI — Botões de Ação

- [ ] 12.1 Adicionar botão "Copiar Dados" que coleta indicadores, formata como CSV e copia para clipboard via pyxclip
- [ ] 12.2 Adicionar botão "Copiar Gráfico" que identifica gráfico ativo, renderiza como PNG e copia para clipboard via comandos nativos (xclip/win32/osascript)

## 13. Clipboard — Exportação de Imagem

- [ ] 13.1 Implementar `clipboard_image.py` (em `infrastructure/` ou `presentation/gui/`): função `copy_image_to_clipboard(figure)` que detecta `sys.platform` e usa o comando apropriado
- [ ] 13.2 Implementar branch Linux: salvar PNG em `/tmp/`, executar `xclip -selection clipboard -t image/png -i`
- [ ] 13.3 Implementar branch Windows: usar `ctypes.windll` + `win32clipboard` ou fallback PowerShell
- [ ] 13.4 Implementar branch macOS: usar `osascript` para setar clipboard com imagem PNG
- [ ] 13.5 Adicionar tratamento de erro com mensagem descritiva caso comando nativo não esteja disponível (ex: xclip não instalado)

## 14. Atalho Desktop

- [ ] 14.1 Implementar `presentation/cli.py` (ou módulo separado): função `create_desktop_shortcut()` que só executa no Linux
- [ ] 14.2 Gerar arquivo `flowscope.desktop` em `~/Desktop/` ou `~/Área de Trabalho/` com `Name=FlowScope`, `Exec=<caminho>`, `Type=Application`, `Terminal=false`, `Icon=<icone>`
- [ ] 14.3 Exibir mensagem de sucesso ou erro (permissão) após tentativa de criação

## 15. Testes

- [ ] 15.1 Criar `tests/test_domain/test_indicators.py`: testes unitários para CVD, VWAP, Volume Profile com dados mock
- [ ] 15.2 Criar `tests/test_domain/test_value_objects.py`: testes para validação de Price, Volume, Ticker
- [ ] 15.3 Criar `tests/test_infrastructure/test_b3_calendar.py`: testes para fibonacci_dates com diferentes datas de referência, incluindo fins de semana
- [ ] 15.4 Criar `tests/test_infrastructure/test_b3_parser.py`: testes para parse_csv com CSV de exemplo (incluindo o sample fornecido), tratamento de linhas vazias
- [ ] 15.5 Criar `tests/test_infrastructure/test_cache.py`: testes para CacheManager (put, get, cache_dir por plataforma)
- [ ] 15.6 Criar `tests/test_presentation/test_cli.py`: testes para argparse flags e dispatch
- [ ] 15.7 Criar `tests/conftest.py`: fixtures compartilhadas (sample CSV content, mock B3Client, mock Tk)

## 16. Verificação e Integração

- [ ] 16.1 Executar `make test` e garantir que todos os testes passam
- [ ] 16.2 Executar `make build` e verificar se PyInstaller gera executável funcional em `dist/`
- [ ] 16.3 Testar fluxo CLI: `python3 -m flowscope --help`, `--version`, `--vwap`, `--cvd`
- [ ] 16.4 Testar fluxo GUI: abrir janela, selecionar data, verificar gráficos, testar load/save de tickers
- [ ] 16.5 Testar clipboard: copiar dados CSV e gráfico no Linux
- [ ] 16.6 Testar `--create-shortcut` no Linux (verificar `.desktop` criado)
- [ ] 16.7 Executar `python3 -m pytest` para garantir cobertura dos cenários spec
