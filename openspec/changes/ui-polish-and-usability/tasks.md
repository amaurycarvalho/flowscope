## 1. Ícone da aplicação

- [x] 1.1 Criar ToolTip class em `presentation/gui/widgets/tooltip.py` com bind Enter/Leave e Toplevel transient
- [x] 1.2 Adicionar ícone à janela: carregar `flowscope.png` (Linux) ou `flowscope.ico` (Windows) de `src/flowscope/icons/` com fallback silencioso se ausente

## 2. Loading guard

- [x] 2.1 Extrair `_enter_loading_state()` — desabilita botão Carregar, desabilita DateEntry, cursor "watch"
- [x] 2.2 Extrair `_exit_loading_state()` — reabilita tudo, restaura cursor
- [x] 2.3 Envolver corpo de `_on_load_data()` em try/finally com enter/exit loading state

## 3. Atalhos de teclado

- [x] 3.1 Bind `<Return>` no DateEntry para acionar `_on_load_data`
- [x] 3.2 Bind `<Control-c>` para `_copy_data`
- [x] 3.3 Bind `<F5>` para recarregar (chamar `_on_load_data`)
- [x] 3.4 Bind `<Destroy>` ou protocolo para salvar preferências ao fechar

## 4. Statusbar com ícones e mensagens temporárias

- [x] 4.1 Adicionar ícones Unicode nas mensagens: `_set_status()` aceitar parâmetro `icon="✓"` etc.
- [x] 4.2 Implementar `_flash_status(msg, icon, clear_ms=2500)` com `after()` e `after_cancel()` para auto-limpeza
- [x] 4.3 Substituir chamadas diretas a `_set_status` por `_flash_status` nas operações de sucesso

## 5. Tooltips, cursor de mão e foco inicial

- [x] 5.1 Adicionar tooltips nos radio buttons (VWAP, CVD, Dispersão), botões (Carregar, Copiar Dados, Copiar Gráfico) e campos
- [x] 5.2 Adicionar `cursor="hand2"` em todos os botões e radio buttons
- [x] 5.3 Chamar `self._date_entry.focus_set()` no final de `__init__`

## 6. Contador de tickers e data carregada

- [x] 6.1 Adicionar label "Tickers (N)" acima ou ao lado do campo de tickers, atualizado em `set_tickers()`
- [x] 6.2 Adicionar label "Exibindo M de N ativos" quando filtro ativo, atualizado em `_on_ticker_edit()`
- [x] 6.3 Adicionar label "Dados: YYYY-MM-DD" na top bar após carregamento

## 7. Agrupamento visual (LabelFrame) e consistência de padding

- [x] 7.1 Envolver radio buttons do seletor de gráfico em `ttk.LabelFrame(self, text="Visualização")`
- [x] 7.2 Envolver botões de ação em `ttk.LabelFrame(self, text="Exportação")`
- [x] 7.3 Definir constantes `PAD_SMALL=4`, `PAD=8`, `PAD_LARGE=12` e substituir todos os valores literais de padx/pady
- [x] 7.4 Adicionar `ipadx=8, ipady=2` nos botões de ação e `ttk.Separator` entre eles
- [x] 7.5 Aplicar `ttk.Style()` para garantir que LabelFrames combinem com o tema atual

## 8. Título dinâmico da janela

- [x] 8.1 Atualizar `self.title()` após `_on_load_data` com formato "FlowScope — YYYY-MM-DD — N ativos"
- [x] 8.2 Atualizar título também após filtro: "FlowScope — YYYY-MM-DD — M de N ativos"

## 9. Double-click e menu de contexto na lista de tickers

- [x] 9.1 Bind `<Double-Button-1>` no campo de texto para selecionar palavra sob o cursor e aplicar filtro
- [x] 9.2 Criar menu de contexto (`tk.Menu(tearoff=0)`) com Copiar, Remover, Selecionar todos, Limpar seleção
- [x] 9.3 Bind `<Button-3>` no campo de texto para exibir o menu de contexto

## 10. Confirmação de cópia e mensagens de erro amigáveis

- [x] 10.1 Usar `_flash_status()` nas funções `_copy_data` e `_copy_chart` em vez de `_set_status()`
- [x] 10.2 Melhorar exibição de erro em `_on_load_data`: capturar exceção, mostrar "⚠ Não foi possível carregar os dados." com descrição curta
- [x] 10.3 Implementar mensagem de empty state no gráfico: "Nenhum ticker corresponde ao filtro."

## 11. Indicador de processamento animado

- [x] 11.1 Criar método `_animate_loading()` com ciclo de pontos via `after()`: "Carregando." → "Carregando.." → "Carregando..."
- [x] 11.2 Chamar `_animate_loading()` em `_enter_loading_state()` e cancelar em `_exit_loading_state()`

## 12. Preferências persistentes

- [x] 12.1 Criar função utilitária `load_preferences()` → retorna dict do `~/.flowscope/config.json` (defaults se não existir ou estiver corrompido)
- [x] 12.2 Criar função utilitária `save_preferences(data)` → escreve JSON em `~/.flowscope/config.json`
- [x] 12.3 No `__init__`, carregar preferências: restaurar geometria da janela, data selecionada, último gráfico, posição do sash
- [x] 12.4 Salvar preferências no fechamento da janela (`WM_DELETE_WINDOW`) e após mudanças de data/gráfico
