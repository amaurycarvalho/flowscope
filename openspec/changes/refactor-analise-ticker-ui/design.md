## Context

O FlowScope usa tkinter com matplotlib para visualização de indicadores de order flow. A aba "Análise do Ticker" possui atualmente:

- Um `ttk.Combobox` para selecionar qual ticker analisar entre os carregados
- Um `ttk.Notebook` com sub-abas de indicadores
- A sub-aba "Evolução da Dominância" usa `DominanceTimelineChart` que tem um painel lateral de resumo (`tk.Text`), uma linha de eficiência via `twiny()`, e tooltips básicos nas barras
- A lista de tickers no painel direito (`TickerList`) já tem suporte a multi-seleção via `Listbox` com `selectmode=EXTENDED`, e dispara `_on_change()` (`_on_ticker_edit` no app.py) sempre que a seleção muda

A TickerList já notifica mudanças de seleção via `_on_listbox_select` → `_on_change`, então o combobox é desnecessário — a informação de qual ticker analisar pode vir diretamente da lista.

## Goals / Non-Goals

**Goals:**

- Eliminar o combobox da aba "Análise do Ticker", derivando o ticker analisado da seleção na TickerList
- Reordenar as sub-abas: "Evolução da Dominância" como primeira aba
- Redesenhar o `DominanceTimelineChart`: remover painel lateral, remover linha de eficiência, enriquecer tooltips, adicionar percentuais nos labels de compradores/vendedores
- Garantir que a troca de seleção na TickerList atualize as abas da "Análise do Ticker" via lazy refresh (mesmo mecanismo existente)

**Non-Goals:**

- Alterar o funcionamento da "Análise Geral" ou seus charts
- Alterar o mecanismo de carregamento de dados ou a TickerList
- Alterar outros charts (VWAPHistChart, QuadrantChart, DominanceRankingChart)
- Adicionar novas funcionalidades além do escopo descrito

## Decisions

### D1: Derivação do ticker via `_get_selected_ticker()`

Nova função auxiliar em `FlowScopeGUI`:

```python
def _get_selected_ticker(self) -> str | None:
    selected = self._ticker_list.get_tickers()  # selected no Listbox
    if selected:
        return selected[0]
    all_tickers = self._ticker_list.get_all_listbox_tickers()
    if all_tickers:
        return all_tickers[0]
    return None
```

- `get_tickers()` retorna apenas os itens com `curselection()` no Listbox
- `get_all_listbox_tickers()` retorna todos os tickers da lista independente de seleção
- Se nenhum ticker disponível, retorna `None` → as abas textuais exibem "Selecione um ticker"

**Alternativa considerada**: Adicionar um atributo `_selected_ticker` que é explicitamente setado. Rejeitada porque duplica estado e a TickerList já gerencia a seleção.

### D2: Lazy refresh via mecanismo existente

O fluxo atual já funciona:

1. Usuário clica em ticker na TickerList
2. `_on_listbox_select` → `_on_change` → `_on_ticker_edit`
3. `_on_ticker_edit` seta `_charts_dirty = True` e chama `_refresh_current_tab()`
4. Se estiver na aba "Análise do Ticker", `_refresh_current_tab()` chama `_update_ticker_indicator_tabs()`
5. `_update_ticker_indicator_tabs()` chama `_get_selected_ticker()` em vez de `self._ticker_combo.get()`

Mudanças necessárias no `_on_ticker_edit`:
- Remover `self._ticker_combo["values"] = tickers` (combobox será removido)
- Manter `self._tickers = list(tickers)` se usado em outro lugar (verificar dependências)
- `_charts_dirty = True` e `_refresh_current_tab()` permanecem

### D3: Reordenação das sub-abas

Simples rearranjo em `tab_configs` (app.py ~linha 244):

```python
tab_configs = [
    ("Evolução da Dominância", "clv", "daily_efficiency", "dominance_score", "daily_money_flow"),
    ("Amplitude de Preço", "range", "range_percentual", "typical_price", "median_price", "weighted_close"),
    ...  # demais inalterados
]
```

O código que cria os frames itera sobre `tab_configs` e usa `name == "Evolução da Dominância"` para decidir se cria chart ou text widget — funciona independente da posição.

A ordem dos textos de ajuda em `_tab_content` é irrelevante (dicionário), mas convém reordenar para clareza de manutenção.

### D4: Redesenho do DominanceTimelineChart

O chart atual tem os seguintes elementos removidos/alterados:

| Elemento | Ação |
|---|---|
| `_summary_frame` + `_summary_text` | Remover |
| `_update_summary()` | Remover método e chamada |
| `twiny()` + `_eff_line` (linha azul de eficiência) | Remover |
| `self._canvas.get_tk_widget().pack(side=tk.LEFT)` | Mudar para `pack(fill=tk.BOTH, expand=True)` (sem `side=LEFT`, já que não tem painel direito) |
| Tooltip atual (`_show_tooltip`) | Expandir para incluir label de Dominância, CLV, label de Convicção, Eficiência em %, MFV diário |
| Labels "Compradores" e "Vendedores" | Adicionar percentual de pregões |

**Tooltip novo**:
```
Data: 2025-01-10
Dominância: Compra Forte (CLV: +0.52)
Convicção: Moderada (Efic: 45,0%)
MFV do pregão: R$ 480.000
```

**Labels no chart**:
```python
self._axes.text(0.95, -0.10, f"Compradores {buyer_pct:.0f}% →", ...)
self._axes.text(0.05, -0.10, f"← Vendedores {seller_pct:.0f}%", ...)
```

Cálculo: `buyer_pct = sum(CLV > 0) / total * 100`, `seller_pct = sum(CLV < 0) / total * 100`. Pregões neutros (CLV == 0) não são contabilizados em nenhum lado (mesmo comportamento do summary atual).

## Risks / Trade-offs

- **[R1] Dependência de ordem na TickerList**: Se o usuário selecionar múltiplos tickers, apenas o primeiro (por ordem de aparição no Listbox) é usado na "Análise do Ticker". Se o primeiro selecionado não for o desejado, o usuário precisa ajustar a seleção. Mitigação: o refresh é imediato ao clicar em outro ticker.
- **[R2] Perda do indicador visual de qual ticker está sendo analisado**: O combobox mostrava explicitamente o ticker. Agora o ticker analisado aparece apenas no título do chart (dentro do matplotlib). Mitigação: já está no título do chart; as abas textuais terão o ticker no header do texto. Resposta do usuário confirmou que é suficiente.
- **[R3] Informação agregada perdida**: O painel lateral mostrava total MFV do período e contagem de pregões compradores. Essas informações agregadas (não por barra) deixam de existir. O usuário optou por manter o status quo (não exibir agregados), apenas os percentuais nos labels.

## Open Questions

- *(nenhuma — todas as decisões foram tomadas na exploração)*
