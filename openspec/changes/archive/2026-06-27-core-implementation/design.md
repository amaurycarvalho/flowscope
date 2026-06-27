## Context

FlowScope é um projeto greenfield — zero linhas de código. Existe apenas a estrutura de repositório (README, CHANGELOG, LICENSE, ícones, diretórios `.opencode/` e `.github/`) e uma especificação de requisitos detalhada. O projeto será desenvolvido em Python 3.10+, com interface gráfica Tkinter + matplotlib e interface CLI via argparse, empacotado com PyInstaller para distribuição multiplataforma (Linux, Windows, macOS). Textos em português.

## Goals / Non-Goals

**Goals:**
- Estabelecer estrutura de diretórios Clean Architecture (domain, application, infrastructure, presentation) com `src/flowscope/`, `tests/` e `pyproject.toml`
- Implementar ingestão de dados da B3 via API two-step com janela temporal Fibonacci
- Calcular indicadores CVD, VWAP e Volume Profile a partir de dados consolidados
- Fornecer interfaces CLI e GUI completas conforme requisitos
- Exportar dados CSV e gráficos para clipboard
- Criar atalho desktop no Linux
- Atualizar artefatos de build (Makefile, flowscope.spec, README)

**Non-Goals:**
- Motor de inferência para estratégias de fluxo (change futura)
- Workflow CI/CD no GitHub Actions (pode ser change separada)
- Suporte a fontes de dados que não a B3
- Internacionalização (i18n) — apenas português
- Persistência de indicadores calculados além do cache temporário de CSVs

## Decisions

### 1. Estrutura de diretórios: Clean Architecture tradicional

**Escolha**: Organização por camada (`domain/`, `application/`, `infrastructure/`, `presentation/`) dentro de `src/flowscope/`.

**Alternativa considerada**: Organização por feature (`data/`, `indicators/`, `strategies/`, `ui/`).

**Rationale**: Clean Architecture por camada alinha-se com a solicitação explícita do spec. Para um projeto que começará com ~7 capabilities bem definidas mas crescerá com motor de inferência e possivelmente novos indicadores, a separação clara entre domínio (regras de negócio), aplicação (casos de uso), infraestrutura (I/O) e apresentação (UI) evita acoplamento e facilita testes unitários do domínio sem dependências externas.

Estrutura resultante:
```
src/flowscope/
├── domain/                  # Entidades, value objects, indicadores
│   ├── entities.py
│   ├── indicators.py
│   └── value_objects.py
├── application/             # Casos de uso e portas (interfaces)
│   ├── use_cases.py
│   └── ports.py
├── infrastructure/          # Implementações concretas
│   ├── b3/
│   │   ├── client.py        # HTTP two-step para API B3
│   │   ├── parser.py        # CSV → domain entities
│   │   └── calendar.py      # Janela Fibonacci com ajuste
│   └── cache.py             # Cache local de CSVs (~/.cache/flowscope/)
├── presentation/            # CLI e GUI
│   ├── cli.py
│   ├── gui/
│   │   ├── app.py
│   │   ├── widgets/
│   │   └── charts/
│   └── main.py
├── icons/                   # Movido de raiz para dentro do pacote
└── __init__.py
```

### 2. Dependência de dados: pandas vs csv stdlib

**Escolha**: Usar módulo `csv` da stdlib para parsing, sem pandas.

**Alternativa considerada**: pandas para parsing e manipulação de dados.

**Rationale**: Os arquivos consolidados da B3 têm ~1.5MB cada (não os ~200MB temidos inicialmente). Com janela Fibonacci de 8 dias, o volume total é ~12MB — trivial para `csv.DictReader`. Evitar pandas:
- Reduz binário PyInstaller em ~100MB
- Remove dependência pesada de instalação
- Operações de agregação por ticker são simples (dicionários, `statistics.mean`, somatórios)

### 3. Cache de CSVs

**Escolha**: Cache em `~/.cache/flowscope/` (Linux), `%LOCALAPPDATA%/flowscope/cache/` (Windows), `~/Library/Caches/flowscope/` (macOS). Arquivos mantidos em CSV original, nomeados por data (`YYYY-MM-DD.csv`). Invalidar quando data de referência muda.

**Alternativa considerada**: Cache em diretório temporário (`/tmp`, `%TEMP%`) que o SO limpa automaticamente.

**Rationale**: Diretório de cache específico da aplicação evita re-download se usuário executar múltiplas vezes na mesma data. `/tmp` pode ser limpo entre execuções. O cache é volátil (redownload quando data muda), então não precisa de lógica complexa de expiração.

### 4. CLI: argparse com subcomandos implícitos

**Escolha**: argparse com flags mutuamente informativas (`--gui`, `--vwap`, `--cvd`, etc.) processadas via `main.py` que decide o fluxo. Sem subcomandos explícitos.

**Alternativa considerada**: argparse com subparsers (`flowscope gui`, `flowscope export vwap`).

**Rationale**: O spec define flags simples (`--gui`, `--vwap`, `--cvd`), não subcomandos aninhados. Manter como flags planas é mais natural para o usuário e compatível com o help já documentado no README. O dispatch é feito em `main.py`: se `--gui`, abre janela; se `--vwap`/`--cvd`, exporta e sai; senão, executa CLI padrão.

### 5. GUI: integração Tkinter + Matplotlib

**Escolha**: `matplotlib.backends.backend_tkagg.FigureCanvasTkAgg` para embutir gráficos matplotlib em frames Tkinter. `tkcalendar.DateEntry` para seleção de data.

**Alternativa considerada**: PyQt/PySide com gráficos nativos.

**Rationale**: Tkinter está definido no spec. É stdlib (sem dependência extra de ~50MB como PyQt), cross-platform, e a integração com matplotlib via `FigureCanvasTkAgg` é madura e bem documentada. tkcalendar cobre o datepicker que Tkinter não tem nativamente.

### 6. Clipboard de imagem: abordagem por plataforma

**Escolha**: Detectar SO via `sys.platform` e usar comandos nativos:
- Linux: salvar PNG temporário, `xclip -selection clipboard -t image/png -i <file>`
- Windows: `ctypes.windll` + `win32clipboard` via `PIL.ImageGrab` (fallback: salvar e usar PowerShell)
- macOS: `osascript -e 'set the clipboard to (read file "...")'` ou `pbcopy`

**Alternativa considerada**: Biblioteca única cross-platform como `clipboard` ou `pyperclip`.

**Rationale**: Nenhuma biblioteca Python suporta clipboard de imagem cross-platform de forma confiável. pyxclip cobre texto; para imagem, ctypes + comandos nativos é a abordagem mais leve e não adiciona dependências. O spec menciona ctypes explicitamente para este fim.

### 7. Seleção de tickers padrão

**Escolha**: Após download e parse de todos os CSVs da janela Fibonacci, agregar `NtlFinVol` (volume financeiro nocional) por ticker, ordenar decrescente, selecionar top 15. Se menos de 15 tickers disponíveis, usar todos.

**Alternativa considerada**: Usar `TradQty` (número de negócios) ao invés de `NtlFinVol`.

**Rationale**: `NtlFinVol` (volume financeiro) é a métrica padrão de mercado para ranquear liquidez. `TradQty` pode favorecer ativos com muitas negociações de baixo valor.

### 8. Fibonacci com ajuste para dias úteis

**Escolha**: Para cada offset (1, 2, 3, 5, 8, 13, 21), subtrair da data de referência. Se a data resultante cair em fim de semana ou feriado, avançar dia a dia até encontrar o próximo dia útil (aproximação local, não em cadeia). A B3 publica arquivos apenas em dias úteis — se não houver arquivo para uma data (ex: feriado), o download retornará erro e o sistema pula esse dia.

**Alternativa considerada**: Ajuste em cadeia (cada offset recalculado a partir da data ajustada do offset anterior).

**Rationale**: Ajuste local é mais simples e preserva a intenção original dos offsets (proximidade temporal à data de referência). Ajuste em cadeia faria os offsets mais distantes (d-21) se deslocarem significativamente, perdendo a propriedade da sequência Fibonacci.

## Risks / Trade-offs

- **[Risco] API B3 pode mudar formato de resposta ou endpoints** → Mitigação: Isolar toda lógica HTTP em `infrastructure/b3/client.py` com interface bem definida em `application/ports.py`. Se a API mudar, só o adapter muda.
- **[Risco] CSV consolidado não contém direção de trade (buyer/seller initiated)** → O cálculo de CVD tradicional requer direção agressor. Sem isso, o indicador será uma aproximação baseada em variação de preço ou delta implícito. Isso precisa ser validado com o usuário na implementação.
- **[Risco] Volume Profile sem dados de price-level granular** → Dados consolidados têm apenas MinPric/MaxPric/TradAvrgPric, não distribuição de volume por nível de preço. Volume Profile pode precisar de aproximação ou ser repensado.
- **[Trade-off] Sem pandas = operações manuais de agregação** → Código mais verboso para group-by e somatórios, mas binário muito menor e inicialização mais rápida. Para ~12MB de dados, performance não é problema.
- **[Trade-off] Tkinter parece datado visualmente** → Aceitável para ferramenta de análise quantitativa onde funcionalidade > estética. Matplotlib oferece gráficos de qualidade profissional.

## Open Questions

- Algoritmo exato de CVD a partir de dados consolidados (sem tick data direcional): quando implementar, validar com o usuário se a abordagem de aproximação por delta de preço é aceitável.
- Volume Profile: definir buckets de preço (tick size do ativo, como decidido) e estratégia para distribuir volume entre MinPric e MaxPric quando só temos agregados.
- Feriados da B3: hardcoded ou consultar API de calendário? Para MVP, lista hardcoded dos feriados nacionais é suficiente.
