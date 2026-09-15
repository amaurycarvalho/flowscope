## 1. Dados e amostragem

- [x] 1.1 Criar `presentation/gui/charts/fundamental_evolution_data.py` com a seleção Fibonacci acumulada das datas (gaps 1..377, aproximação para a data de cache mais próxima, extremos sempre incluídos, sem duplicatas, saída crescente) e verificar com teste unitário cobrindo cache denso, cache esparso e menos de três datas
- [x] 1.2 Adicionar ao mesmo módulo a montagem das séries dos sete campos a partir das observações datadas, produzindo lacunas para valores ausentes e indicando campo sem nenhum valor, e verificar com teste unitário cobrindo campo presente, campo parcialmente ausente e campo totalmente ausente
- [x] 1.3 Garantir que a montagem consome apenas observações fornecidas (sem I/O) e verificar com teste que nenhuma chamada de rede/armazenamento é feita

## 2. Painel gráfico

- [x] 2.1 Criar `presentation/gui/charts/fundamental_evolution_panel.py` com os sete small multiples (linha por campo, eixo de datas real compartilhado, escala vertical própria, destaque e anotação do valor mais recente) e verificar com teste de fumaça que a figura é montada sem erro para séries completas
- [x] 2.2 Integrar o estado vazio (`create_empty`/`show_empty`/`hide_empty`) para ticker sem histórico e verificar que o rótulo aparece quando não há observações e some quando há
- [x] 2.3 Formatar os valores por campo reaproveitando `fundamental_formatters` (reais, percentual, quantidade/inteiro) e verificar com teste que cada painel recebe a unidade correta
- [x] 2.4 Adicionar a barra `ToolbarBR` com o botão "Copiar Gráfico" e verificar que o callback de cópia é acionado

## 3. Integração na GUI

- [x] 3.1 Adicionar a sub-aba "Evolução dos Fundamentos" em `TAB_CONFIGS` e `ENABLED_TABS` e construir o painel em `_build_ticker_tabs` (`app_tab_layout.py`), registrando-o em `_TICKER` e `_all_charts` (`app_layout.py`), e verificar que a sub-aba aparece ativa ao navegar para "Análise do Ticker"
- [x] 3.2 Adicionar `on_row_activated(ticker)` a `FundamentalTablePanel` e associá-lo a `<Double-1>` nos dois `Treeview`, e verificar com teste que o callback recebe o ticker da linha clicada
- [x] 3.3 Implementar o handler de duplo clique na GUI: fixar `_evolution_ticker`, selecionar a aba "Análise do Ticker" e a sub-aba "Evolução dos Fundamentos", e verificar que a sub-aba fica ativa com o ticker clicado
- [x] 3.4 Guardar `self._fundamental_history_store` em `_wire_controller` (`app.py`) e adicionar o caso do painel de evolução em `_do_update` (`app_actions.py`), lendo `datas`/`historico` e chamando o montador, e verificar que o painel é preenchido a partir do cache
- [x] 3.5 Escapar do gate de `_current_data` em `_on_tab_changed` apenas para o painel de evolução e verificar com teste que a evolução é preenchida sem dados B3 carregados
- [x] 3.6 Usar `_evolution_ticker` com fallback para o ticker selecionado na `TickerList`, limpando o pin em `on_ticker_edit`, e verificar que o painel segue a seleção após a troca de ticker
- [x] 3.7 Adicionar a entrada de `TAB_CONTENT` para `("Análise do Ticker", "Evolução dos Fundamentos")` no padrão explicativo (objetivo, pergunta, indicadores, como interpretar) e verificar que o OrientationPanel exibe o conteúdo ao selecionar a sub-aba

## 4. Documentação e validação

- [x] 4.1 Descrever a nova sub-aba em `panels.md` (objetivo, pergunta, campos, small multiples, amostragem Fibonacci e interpretação) e verificar a consistência com o texto orientativo
- [x] 4.2 Executar `openspec validate evolucao-fundamentos --strict` e corrigir qualquer pendência
- [x] 4.3 Executar `make lint` e `make test` e garantir cobertura mínima de 85% sem regressões
