## Context

O carregamento de dados no FlowScope é um pipeline síncrono de múltiplas etapas:

```
1. Obter datas disponíveis (Fibonacci: 7 dates)
2. Para cada data: fetch HTTP → parse CSV → filtrar tickers
3. Executar motor de indicadores (DAG) sobre os trades filtrados
4. Montar resultado por ticker
```

A statusbar atual usa um `tk.Label` com `StringVar` e uma animação textual cega (`_animate_loading`). O carregamento bloqueia a thread principal do Tkinter — não há como reportar progresso intermediário sem um mecanismo explícito.

## Goals / Non-Goals

**Goals:**
- Exibir barra de progresso determinate (`ttk.Progressbar`) na statusbar durante carregamento de dados
- Exibir label textual lado a lado com a barra descrevendo a etapa atual
- Reportar progresso granular: por data baixada, por fase de processamento, por portfolio carregado
- Dados em cache devem refletir progresso completo (não pular nem travar)
- Falhas em datas devem ser contabilizadas no progresso
- Portfolio loading deve aparecer como etapa textual na progressão
- Manter compatibilidade com o código existente — mudanças são aditivas

**Non-Goals:**
- Não mover o carregamento para thread separada (escopo futuro)
- Não adicionar botão de cancelamento
- Não modificar a lógica de cache existente
- Não alterar o comportamento do CLI
- Não alterar a aparência geral da statusbar além do progresso

## Decisions

### Decision: Progress callback como classe `ProgressReporter`

Criar uma classe `ProgressReporter` que carrega o estado do progresso e é passada como dependência opcional através das camadas.

```python
@dataclass
class ProgressStep:
    label: str          # "Baixando dados históricos"
    current: int        # passo atual dentro da fase
    total: int          # total de passos da fase
    weight: int = 1     # peso relativo desta fase no progresso global

class ProgressReporter:
    _phases: list[ProgressStep]
    _on_update: Callable[[int, int, str], None]  # current, total, label

    def start_phase(self, label, total, weight=1): ...
    def advance(self, n=1, detail=""): ...
    def fail(self, n=1, detail=""): ...
    def finish_phase(self): ...
```

**Rationale**: Um objeto separado é testável, pode ser substituído por um mock em testes, e não acopla a GUI às camadas de domínio/infra. O callback `_on_update` ponteia para a thread principal.

**Alternativa considerada**: Callback avulso `(current, total, message)`. Rejeitado porque não gerencia fases automaticamente — o código cliente precisaria calcular proporções manualmente.

### Decision: Pesos relativos por fase

O progresso global é calculado como proporção ponderada das fases:

```
Fase                     Peso  Passos
Carregar portfólio        1    1 (se necessário)
Download de datas         3    7 datas
Processar indicadores     2    N tickers
```

O peso reflete a duração relativa estimada de cada fase. Uma fase concluída conta como `peso * 100% / soma_pesos`.

**Rationale**: Fases com pesos diferentes (download é mais lento que processamento) produzem uma barra mais realista.

**Alternativa considerada**: Passos lineares (cada data = 1 passo, cada ticker = 1 passo). Rejeitado porque 7 datas + 87 tickers faria o progresso pular de 7% para 93% na transição entre fases.

### Decision: Widget na statusbar — `ttk.Progressbar` + `tk.Label`

Substituir o `tk.Label` atual por um `tk.Frame` contendo:

```
┌──────────────────────────────────────────────────┐
│ [ ⏳ Baixando dia 3/7  ████████░░░░  57% ]       │
└──────────────────────────────────────────────────┘
```

Layout: `tk.Frame` (side=BOTTOM, fill=X) → `tk.Label` (texto) + `ttk.Progressbar` (modo 'determinate', expand=True, fill=X).

**Rationale**: `ttk.Progressbar` no modo determinate é o widget nativo do Tk para barras de progresso. O label ao lado fornece contexto textual. Ambos dentro de um Frame permitem flexibilidade de layout.

**Alternativa considerada**: `ttk.Progressbar` sozinho com texto via `sys.stderr`. Rejeitado — perderia a integração visual com a statusbar.

### Decision: Sistema de fases para o pipeline de carregamento

As fases do pipeline são mapeadas explicitamente:

```python
class LoadingPhase(IntEnum):
    PORTFOLIO = 0    # "Baixando portfólio..."
    FETCH_DATA = 1   # "Baixando dados históricos"
    PROCESSING = 2   # "Processando indicadores"
    DONE = 3         # "Pronto."
```

Cada fase tem um peso e total conhecido. O `ProgressReporter` gerencia a transição entre fases automaticamente.

**Rationale**: Fases explícitas permitem que o código em diferentes camadas reporte progresso sem conhecer a estrutura geral do pipeline.

### Decision: Cache — datas em cache são "avanço zero-time"

Se `B3Client.fetch_file()` encontra dado em cache, ele avança o progresso imediatamente (sem delay). O efeito visual é a barra preenchendo rapidamente quando todos os dados estão em cache.

**Rationale**: O usuário vê o progresso completo mesmo quando tudo está em cache, confirmando que nenhum download foi necessário. Sem essa decisão, a barra ficaria parada em 0% e pularia para "Pronto." — o que seria confuso.

## Risks / Trade-offs

- **[Reentrância no event loop]** O callback `_on_update` chama `self.update_idletasks()` para redesenhar a barra — isso pode causar processamento de eventos aninhados se o callback for invocado de dentro de um handler. Mitigação: usar `after(0, ...)` no callback para agendar na fila de eventos, mas isso requer que o loop principal retorne à event loop — o que não acontece enquanto o carregamento síncrono está rodando. **Solução**: chamar `self.update()` (não apenas `update_idletasks()`) dentro do callback para forçar um redesenho durante o carregamento síncrono.
- **[Performance]** Chamar `update()` a cada avanço de progresso (potencialmente centenas de vezes) pode tornar o carregamento mais lento. Mitigação: agrupar avanços — o callback só atualiza a GUI se `progresso_atual - progresso_exibido > 1%` ou se passaram >100ms desde a última atualização.
- **[Falha em datas]** O `fetch_trades` já trata exceções por data e continua. O progresso precisa contar a data como "processada" mesmo em falha, mas o label pode indicar "3/7 (1 falhou)". Mitigação: o `ProgressReporter.advance()` aceita um parâmetro `failed=False`; quando True, o label inclui a contagem de falhas.
