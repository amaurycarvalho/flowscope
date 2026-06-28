## Context

Atualmente os botões "Copiar Dados" e "Copiar Gráfico" estão agrupados num `LabelFrame("Exportação")` dentro do `self._left_pw` (PanedWindow vertical esquerdo), abaixo do notebook de abas. Isso foi uma melhoria recente que resolveu o problema do frame ficar escondido, mas a solução ideal é realocar cada botão para seu lugar semântico:

- "Copiar Gráfico" → toolbar nativo do matplotlib (ação do chart)
- "Copiar Dados" → barra superior, ao lado de "Carregar" (ação global, depende de dados carregados)

O frame Exportação pode então ser eliminado, simplificando o layout.

## Goals / Non-Goals

**Goals:**
- Eliminar o frame Exportação (`LabelFrame` + `btn_container`) do `self._left_pw`
- Adicionar toolitem "Copiar Gráfico" ao `ToolbarBR`
- Adicionar botão "Copiar Dados" na `_build_top_bar()`, desabilitado até o primeiro carregamento
- Manter atalho `Ctrl+Shift+C` para copiar dados
- Manter confirmação visual na statusbar para ambas as cópias

**Non-Goals:**
- Não alterar a lógica de cópia em si (clipboard, pyxclip, fallback)
- Não alterar o atalho de teclado `Ctrl+Shift+C`
- Não adicionar suporte a múltiplos charts simultâneos (cada chart futuro terá seu próprio toolbar)

## Decisions

### 1. ToolbarBR aceita callback de cópia via construtor

Em vez de acoplar `ToolbarBR` ao `FlowScopeGUI`, o toolbar recebe um `copy_chart_callback` opcional. O callback recebe o `Figure` do matplotlib como argumento.

```
ToolbarBR.__init__(self, canvas, parent, copy_chart_callback=None)
    self._copy_chart_callback = copy_chart_callback
    super().__init__(canvas, parent)

def copy_chart(self):          # chamado pelo botão via toolitems
    if self._copy_chart_callback:
        self._copy_chart_callback(self.canvas.figure)
```

**Alternativa considerada:** ToolbarBR receber uma referência direta ao `FlowScopeGUI`. Rejeitada porque acopla o chart ao app, dificultando teste e reuso.

### 2. Toolitem usa ícone existente do matplotlib

O novo toolitem usa o ícone `filesave.png` (já existente no matplotlib) — semanticamente próximo ("salvar figura"). Tooltip: "Copiar gráfico como imagem para a área de transferência".

```python
toolitems = (
    ...
    ("Salvar", "Salvar gráfico como imagem", "filesave", "save_figure"),
    ("Copiar Gráfico", "Copiar gráfico como imagem para a área de transferência", "filesave", "copy_chart"),
)
```

O callback `copy_chart` resolve como método na instância via `getattr(self, 'copy_chart')`.

### 3. Botão "Copiar Dados" na top bar, após "Carregar"

Posicionado à direita de `self._load_button`, com `state=tk.DISABLED` inicial. Habilitado apenas após `_on_load_data()` completar com sucesso.

```python
# _build_top_bar
self._copy_data_btn = tk.Button(top, text="Copiar Dados",
                                command=self._copy_data, state=tk.DISABLED, ...)
self._copy_data_btn.pack(side=tk.LEFT, padx=PAD_SMALL)
```

Ciclo de vida do estado:
| Momento | Estado |
|---|---|
| Inicial (sem dados) | `DISABLED` |
| Durante carregamento | Inalterado |
| Após carregamento bem-sucedido | `NORMAL` |
| Após carregamento com erro | Inalterado (se havia dados antes, continua `NORMAL`) |

### 4. Remoção completa do frame Exportação

O bloco de criação do `export_frame` + `btn_container` + botões + `ttk.Separator` em `_build_main_area()` é removido. A `_build_action_buttons()` permanece como no-op (pode ser removida em limpeza futura).

### 5. Ajuste no estado do Botão durante loading states

`_enter_loading_state` e `_exit_loading_state` não precisam tocar no `_copy_data_btn` — seu estado é gerenciado exclusivamente pelo sucesso/falha do `_on_load_data`.

### 6. Atualização das specs existentes

Dois delta specs:
- `specs/ui-polish/delta.md`: Remove requisitos de LabelFrame Exportação e separador visual entre botões
- `specs/clipboard-export/delta.md`: Esclarece que "Copiar Gráfico" está no toolbar do chart

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| Toolbar do matplotlib pode ficar visualmente apertado com botão extra | O toolbar atual tem 7 botões + 2 separadores. 1 botão extra é aceitável. Monitorar em futuros charts. |
| `ToolbarBR` agora tem dependência de callback (acoplamento fraco) | Callback é opcional (`None` por default). Botão existe mas é no-op sem callback. |
| Botão "Copiar Dados" na top bar pode passar despercebido | Top bar é a primeira coisa que o usuário vê. Posicionado ao lado de "Carregar", fica no fluxo natural. |
| Botão desabilitado sem feedback visual de *por que* está desabilitado | A tooltip pode explicar ("Copiar dados — carregue os dados primeiro"). |
| `_copy_chart` muda de `self._vwap_chart.get_figure()` para `self._canvas.figure` no callback | `self.canvas.figure` é a API padrão do matplotlib e funciona para qualquer chart. |
