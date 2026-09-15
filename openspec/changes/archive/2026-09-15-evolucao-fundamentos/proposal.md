## Why

O cache histórico de fundamentos por `(ticker, data)` já existe e foi desenhado para habilitar a consulta da evolução do ticker, mas nenhuma interface consome essa porta. Hoje o usuário vê apenas o retrato de uma data; não consegue perceber se cotação, patrimônio, dividendos, cotistas e cotas melhoraram ou pioraram ao longo das observações retidas.

## What Changes

- Criar a sub-aba "Evolução dos Fundamentos" na aba "Análise do Ticker", exibindo a evolução temporal (timeseries) dos campos Cotação, VP, P/VP, DY, Último dividendo, Nº de cotistas e Nº de cotas para o ticker selecionado.
- Ler os dados exclusivamente do `JsonFundamentalHistoryStore` (cache fundamental), sem qualquer aquisição de rede ao abrir a sub-aba.
- Amostrar as datas do cache por Fibonacci de forma acumulada a partir da observação mais recente (gaps de 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377 dias), aproximando cada alvo para a data de cache mais próxima e incluindo sempre a mais antiga e a mais recente; exibir as datas em ordem crescente (mais antiga → mais recente).
- Representar os campos em small multiples (um mini-gráfico de linha por campo, eixo X de datas compartilhado e escala própria), preservando a leitura dos valores absolutos por um leigo.
- Permitir que o duplo clique em uma linha da tabela da sub-aba "Fundamentos" (aba "Análise Geral") fixe o ticker e torne ativa a sub-aba "Evolução dos Fundamentos".
- Popular a sub-aba de forma preguiçosa (somente quando selecionada), no mesmo estilo das demais, funcionando apenas com o cache mesmo sem carga B3 corrente.
- Exibir estado vazio quando não houver histórico retido para o ticker e preencher o quadro de texto orientativo da sub-aba no mesmo padrão explicativo das demais.

## Capabilities

### New Capabilities

- `fundamental-evolution-panel`: painel gráfico de evolução dos fundamentos de um ticker a partir do cache histórico, incluindo a amostragem Fibonacci das datas, os small multiples dos sete campos, o estado vazio e a formatação dos valores.

### Modified Capabilities

- `gui-interface`: a aba "Análise do Ticker" passa a ter a sub-aba "Evolução dos Fundamentos", a tabela de "Fundamentos" da aba "Análise Geral" passa a reagir ao duplo clique ativando essa sub-aba, e o OrientationPanel passa a ter conteúdo para a nova sub-aba.

## Impact

- **Código**: novo painel em `presentation/gui/charts` e um módulo puro de amostragem/séries; callback de duplo clique em `charts/fundamental_table.py`; registro da sub-aba em `app_tab_layout.py`, `app_tabs.py` e `app_layout.py`; atualização preguiçosa em `app_actions.py`; acesso ao store exposto a partir de `app.py`.
- **Dados**: somente leitura de `~/.cache/flowscope/fundamentos/{TICKER}.json`; nenhuma escrita nova.
- **Dependências/APIs**: nenhuma dependência nova; reutiliza `JsonFundamentalHistoryStore`, `empty_state`, `ToolbarBR` e os formatadores de `fundamental_formatters`.
- **Documentação**: `panels.md` passa a descrever a nova sub-aba.
- **Compatibilidade**: aditivo; a porta do cache e o comportamento atual das demais abas não mudam.
