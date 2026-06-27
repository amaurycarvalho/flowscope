## Context

FlowScopeUI gerencia preferências em `~/.flowscope/config.json` com chaves `last_date`, `last_chart`, `window_geometry`, `sash_positions`. O widget `TickerList` atualmente gerencia seus próprios `filedialog` sem qualquer conhecimento do sistema de preferências. O botão "Hoje" (`_on_today`) apenas atualiza o DateEntry — não dispara `_on_load_data`.

## Goals / Non-Goals

**Goals:**
- Botão "Hoje" carrega dados automaticamente (chama `_on_load_data` após `set_date`)
- Diálogos Salvar/Carregar Tickers abrem na última pasta usada
- `last_ticker_dir` é salvo em `~/.flowscope/config.json`
- Baixo acoplamento: `TickerList` não conhece o sistema de preferências

**Non-Goals:**
- Não alterar a estrutura do config.json além de adicionar `last_ticker_dir`
- Não adicionar novas dependências
- Não alterar comportamento do botão "Filtrar", atalhos de teclado, ou outros controles

## Decisions

| Decisão | Opção Escolhida | Alternativa | Motivo |
|---------|----------------|-------------|--------|
| Como TickerList acessa o diretório? | Recebe `initialdir: str | None` e `on_dir_changed: callable` no construtor | TickerList ler/gravar config.json diretamente | Baixo acoplamento: TickerList não depende do sistema de arquivos de config |
| Quem gerencia o callback? | FlowScopeGUI passa `lambda d: save_preferences({**prefs, "last_ticker_dir": d})` | TickerList aceitar string de dir + função separada | Unificado: FlowScopeGUI coordena a persistência |
| Como `_on_today` chama `_on_load_data`? | Adicionar `self._on_load_data()` no fim de `_on_today` | Extrair um método `_load_current_date()` compartilhado | Simplicidade máxima: `_on_today` só faz `set_date` + delega para `_on_load_data` |

### Fluxo: Hoje com carregamento

```
_on_today()
  ├─ self._date_entry.set_date(date.today())
  └─ self._on_load_data()   ← NOVO
       ├─ _enter_loading_state()
       ├─ _ensure_tickers()
       ├─ _use_case.execute(...)
       ├─ _update_charts()
       └─ _exit_loading_state()
```

### Fluxo: Salvar Tickers com last_dir

```
TickerList.__init__(initialdir="/home/user/dados", on_dir_changed=...)
                              ↓
_save()
  └─ filedialog.asksaveasfilename(initialdir=self._initialdir)  ← NOVO
  └─ if path: on_dir_changed(Path(path).parent)                 ← NOVO
  └─ Path(path).write_text(...)
                              ↓
FlowScopeGUI salva em ~/.flowscope/config.json
  └─ on_dir_changed → save_preferences({..., "last_ticker_dir": dir})
```

### Estrutura do config.json

```json
{
  "last_date": "2026-06-27",
  "last_chart": "vwap",
  "window_geometry": "1280x800+100+50",
  "sash_positions": [350, null, null, null],
  "last_ticker_dir": "/home/user/dados"    ← NOVO
}
```

## Risks / Trade-offs

- **TickerList recebe callback, mas nunca o invoca até que o usuário selecione um arquivo** → Sem risco: callback só é chamado após `filedialog` retornar com path válido
- **Se `last_ticker_dir` apontar para um diretório que não existe mais** → `filedialog` aceita `initialdir` inválido silenciosamente (fallback para diretório padrão do SO) — sem necessidade de validação extra
- **Abordagem A (callback) vs B (TickerList acessar config diretamente)** → A foi escolhida para manter TickerList puro, sem dependência do sistema de arquivos ou formato de config
