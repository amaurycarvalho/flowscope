## Context

FlowScope usa `tkinter` para a GUI. A top bar (construída em `app.py:_build_top_bar`) contém botões Hoje, Carregar e Copiar Dados com texto. A sidebar (widget `TickerList` em `ticker_list.py`) tem dois frames de botões: um com Salvar/Carregar/Filtrar e outro com IBOV/IDIV/IFIX.

Pillow (`PIL`) já é dependência do projeto via `pyproject.toml`. Todos os ícones necessários já existem em `src/flowscope/icons/`.

## Goals / Non-Goals

**Goals:**
- Substituir texto dos 6 botões por ícones nos locais especificados
- Manter todos os tooltips existentes e adicionar tooltips aos botões que não têm
- Unificar os dois frames de botões da sidebar em um único layout horizontal
- Redimensionar botões para o tamanho do ícone (20×20 px)

**Non-Goals:**
- Não alterar comportamento, callbacks ou estado dos botões
- Não alterar outros elementos da UI além dos botões mapeados
- Não adicionar novas funcionalidades ou capacidades
- Não modificar tooltips existentes

## Decisions

### 1. Carregamento de ícones com Pillow `ImageTk.PhotoImage`

`tk.PhotoImage` nativo só suporta GIF/PPM. Pillow `ImageTk.PhotoImage` funciona com PNG em qualquer versão Tk.

- Alternativa considerada: converter PNGs para GIF e usar `tk.PhotoImage` diretamente — rejeitada por adicionar step extra de build e degradar qualidade.
- **Decisão**: usar `PIL.Image.open()` + `ImageTk.PhotoImage()`. Armazenar referência como atributo de instância (`self._icon_*`) para evitar garbage collection do tkinter.

### 2. Tamanho uniforme dos ícones

Os PNGs em `src/flowscope/icons/` podem ter tamanhos variados.

- Alternativa considerada: usar tamanho original de cada PNG — rejeitada por possível inconsistência visual.
- **Decisão**: redimensionar todos para 20×20 px com `Image.resize((20, 20), Image.LANCZOS)`.

### 3. Layout da sidebar: fusão dos dois frames

Atualmente:

```
btn_frame:  [Salvar Tickers] [Carregar Tickers] [Filtrar]
btn_frame2: [IBOV] [IDIV] [IFIX]
```

**Decisão**: criar um único `btn_frame` com os 6 botões lado a lado via `pack(side=tk.LEFT)`:

```
btn_frame: [save_icon] [open_icon] [filter_icon] [IBOV] [IDIV] [IFIX]
```

### 4. Tooltips nos botões da sidebar

Apenas os botões da top bar têm `ToolTip` atualmente. Os da sidebar não têm.

**Decisão**: adicionar `ToolTip` aos botões Salvar Tickers ("Salvar lista de tickers em arquivo"), Carregar Tickers ("Carregar lista de tickers de arquivo") e Filtrar ("Filtrar tickers exibidos").

### 5. Construção dos botões via helper

A criação de botões com ícone se repete 6 vezes. Um método auxiliar pode evitar duplicação.

**Decisão**: criar um helper local `_make_icon_button(parent, icon_filename, tooltip, command)` que:
1. Carrega a imagem com `Image.open` + `ImageTk.PhotoImage`
2. Cria o `tk.Button(image=..., padx=0, cursor="hand2", command=...)`
3. Anexa `ToolTip`
4. Armazena e retorna a referência da imagem para manter lifecycle

## Risks / Trade-offs

- **[Garbage collection do tkinter]** `PhotoImage` sem referência persistente desaparece da tela. → Mitigação: armazenar sempre em `self._icon_*` ou em lista `self._icons`.
- **[Tamanho do ícone]** 20×20 pode ser pequeno em monitores HiDPI. → Mitigação: tamanho facilmente ajustável mudando uma constante `ICON_SIZE`.
- **[Plotting]** Pillow já é dependência do projeto, sem risco adicional.

## Open Questions

Nenhuma. Todas as decisões estão claras com base nos requisitos e no código existente.
