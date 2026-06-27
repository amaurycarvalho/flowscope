## Purpose

Define UI polish improvements for FlowScope's main window, covering loading state guards, statusbar icons, auto-clearing messages, ticker counter, keyboard shortcuts, tooltips, cursor styles, visual grouping, consistent padding, empty-state messaging, friendly error messages, dynamic window title, animated processing indicator, context menu, persistent preferences, application icon, initial focus, copy confirmation, double-click filtering, and button separation.

## Requirements

### Requirement: Loading guard
O sistema DEVE desabilitar os botões "Carregar" e "Hoje" e o campo DateEntry durante a execução de `_on_load_data()`, e alterar o cursor para "watch". Ao final (inclusive em caso de erro), DEVE restaurar todos os controles.

#### Scenario: Botões desabilitados durante carregamento
- **WHEN** o usuário clica em "Carregar" ou "Hoje"
- **THEN** ambos os botões DEVEM ser desabilitados e o cursor DEVE mudar para "watch" imediatamente

#### Scenario: Controles restaurados após carregamento
- **WHEN** o carregamento termina (com ou sem erro)
- **THEN** os botões DEVEM ser reabilitados e o cursor DEVE voltar ao normal

### Requirement: Statusbar com ícones de estado
A barra de status DEVE exibir um ícone Unicode antes da mensagem, variando conforme o contexto: ✓ (sucesso), ⏳ (carregando), ⚠ (erro/aviso), ℹ (informativo).

#### Scenario: Ícone de sucesso
- **WHEN** uma operação é concluída com sucesso
- **THEN** a barra DEVE mostrar "✓ <mensagem>"

#### Scenario: Ícone de carregamento
- **WHEN** uma operação demorada está em andamento
- **THEN** a barra DEVE mostrar "⏳ <mensagem>"

### Requirement: Mensagens temporárias na statusbar
O sistema DEVE limpar a mensagem da barra de status automaticamente após 2.5 segundos para mensagens de sucesso.

#### Scenario: Auto-limpeza após cópia
- **WHEN** o usuário copia dados com sucesso
- **THEN** a mensagem "✓ Dados copiados" DEVE ser exibida por 2.5 segundos e depois reverter para "Pronto."

### Requirement: Contador de tickers
O sistema DEVE exibir um contador de tickers ao lado da lista, atualizado automaticamente após carregar dados e após aplicar filtro.

#### Scenario: Contador após carregamento
- **WHEN** 37 tickers são carregados
- **THEN** o sistema DEVE exibir "Tickers (37)" no título da lista

#### Scenario: Contador após filtro
- **WHEN** o usuário filtra para 15 tickers de 37 totais
- **THEN** o sistema DEVE exibir "Exibindo 15 de 37 ativos"

### Requirement: Data carregada visível
O sistema DEVE exibir a data de referência atualmente carregada em algum lugar da interface após o carregamento.

#### Scenario: Data exibida após carregamento
- **WHEN** dados são carregados para a data 2026-06-25
- **THEN** a interface DEVE mostrar "Dados: 2026-06-25"

### Requirement: Atalhos de teclado
O sistema DEVE fornecer atalhos de teclado: Enter para Carregar, Ctrl+C para Copiar Dados, F5 para Recarregar. Os atalhos NÃO DEVEM conflitar com atalhos padrão do sistema operacional.

#### Scenario: Enter aciona Carregar
- **WHEN** o usuário pressiona Enter com o DateEntry focado
- **THEN** o sistema DEVE executar a mesma ação do botão "Carregar"

#### Scenario: F5 recarrega
- **WHEN** o usuário pressiona F5
- **THEN** o sistema DEVE recarregar os dados da data atualmente selecionada

#### Scenario: Ctrl+C copia dados
- **WHEN** o usuário pressiona Ctrl+C
- **THEN** o sistema DEVE copiar os dados CSV para o clipboard

### Requirement: Tooltips nos controles
O sistema DEVE exibir tooltips ao passar o mouse sobre controles: indicadores (VWAP, CVD, Dispersão), botões de ação e campos de entrada.

#### Scenario: Tooltip no VWAP
- **WHEN** o mouse passa sobre o radio button "VWAP"
- **THEN** DEVE exibir "Preço médio ponderado por volume"

#### Scenario: Tooltip no CVD
- **WHEN** o mouse passa sobre o radio button "CVD"
- **THEN** DEVE exibir "Cumulative Volume Delta"

### Requirement: Cursor de mão em botões
Botões e controles interativos DEVEM usar o cursor "hand2".

#### Scenario: Cursor de mão no botão Carregar
- **WHEN** o mouse passa sobre o botão "Carregar"
- **THEN** o cursor DEVE mudar para uma mão

### Requirement: LabelFrame para agrupamento visual
O seletor de gráfico DEVE ser agrupado em um `LabelFrame` com título "Visualização". Os botões de ação DEVEM ser agrupados em um `LabelFrame` com título "Exportação".

#### Scenario: Seletor agrupado
- **WHEN** a interface é renderizada
- **THEN** os radio buttons DEVEM estar dentro de um LabelFrame "Visualização"

#### Scenario: Ações agrupadas
- **WHEN** a interface é renderizada
- **THEN** os botões "Copiar Dados" e "Copiar Gráfico" DEVEM estar dentro de um LabelFrame "Exportação"

### Requirement: Padding consistente
O sistema DEVE usar constantes de padding centralizadas (PAD_SMALL=4, PAD=8, PAD_LARGE=12) em vez de valores numéricos isolados.

#### Scenario: Padding substituído
- **WHEN** a interface é construída
- **THEN** todos os valores de padx/pady DEVEM usar as constantes definidas

### Requirement: Mensagem de ausência de dados
Quando o filtro eliminar todos os tickers, o gráfico DEVE exibir uma mensagem textual em vez de ficar vazio.

#### Scenario: Filtro sem resultados
- **WHEN** o filtro remove todos os tickers
- **THEN** o gráfico DEVE exibir a mensagem "Nenhum ticker corresponde ao filtro."

### Requirement: Mensagens de erro amigáveis
Erros durante carregamento DEVEM ser exibidos na barra de status com o ícone ⚠ e uma mensagem curta e legível, não o stack trace completo.

#### Scenario: Erro de carregamento
- **WHEN** ocorre um erro ao carregar dados
- **THEN** a barra de status DEVE mostrar "⚠ Não foi possível carregar os dados." + breve descrição

### Requirement: Título dinâmico da janela
A janela DEVE ter seu título atualizado após carregar dados e após aplicar filtro, seguindo o formato "FlowScope — YYYY-MM-DD — N ativos".

#### Scenario: Título após carregamento
- **WHEN** dados de 2026-06-25 são carregados com 143 tickers
- **THEN** o título DEVE ser "FlowScope — 2026-06-25 — 143 ativos"

### Requirement: Indicador de processamento animado
Durante o carregamento, a barra de status DEVE mostrar uma animação de pontos usando `after()`.

#### Scenario: Animação durante carregamento
- **WHEN** dados estão sendo carregados
- **THEN** a barra DEVE mostrar "Carregando." → "Carregando.." → "Carregando..." ciclicamente

### Requirement: Menu de contexto na lista de tickers
O campo de tickers DEVE ter um menu de contexto (botão direito) com opções: Copiar ticker, Remover do filtro, Selecionar todos, Limpar seleção.

#### Scenario: Menu de contexto
- **WHEN** o usuário clica com o botão direito no campo de tickers
- **THEN** um menu DEVE aparecer com as opções disponíveis

### Requirement: Preferências persistentes
O sistema DEVE salvar e restaurar a última data selecionada, último gráfico, geometria da janela, posição do divisor do PanedWindow e último diretório dos diálogos de ticker em `~/.flowscope/config.json`.

#### Scenario: Restauração de preferências
- **WHEN** o aplicativo inicia
- **THEN** a janela DEVE restaurar sua geometria, data, e `last_ticker_dir` da última sessão

#### Scenario: Último diretório salvo após salvar tickers
- **WHEN** o usuário clica em "Salvar Tickers" e seleciona um arquivo em `/home/user/dados/tickers.txt`
- **THEN** o diretório `/home/user/dados/` DEVE ser salvo como `last_ticker_dir` em `~/.flowscope/config.json`

#### Scenario: Último diretório salvo após carregar tickers
- **WHEN** o usuário clica em "Carregar Tickers" e seleciona um arquivo em `/home/user/dados/tickers.txt`
- **THEN** o diretório `/home/user/dados/` DEVE ser salvo como `last_ticker_dir` em `~/.flowscope/config.json`

#### Scenario: Diálogo abre no último diretório
- **WHEN** o usuário clica em "Salvar Tickers" ou "Carregar Tickers" e existe `last_ticker_dir` nas preferências
- **THEN** o diálogo DEVE abrir com `initialdir` apontando para `last_ticker_dir`

### Requirement: Ícone da aplicação
O sistema DEVE definir o ícone da janela para aparecer na barra de tarefas, buscando o arquivo apropriado em `src/flowscope/icons/`.

#### Scenario: Ícone definido no Windows
- **WHEN** o aplicativo inicia no Windows e `flowscope.ico` existe
- **THEN** a janela DEVE usar esse ícone via `iconbitmap()`

#### Scenario: Ícone definido no Linux
- **WHEN** o aplicativo inicia no Linux e `flowscope.png` existe
- **THEN** a janela DEVE usar esse ícone via `wm_iconphoto()`

### Requirement: Foco inicial no DateEntry
Ao abrir, o campo DateEntry DEVE receber o foco do teclado.

#### Scenario: Foco no DateEntry
- **WHEN** a interface é carregada
- **THEN** o DateEntry DEVE estar com o foco para digitação

### Requirement: Confirmação visual de cópia
Após copiar dados ou gráfico, o sistema DEVE mostrar "✓ Dados copiados" ou "✓ Gráfico copiado" na barra de status e reverter para "Pronto." após 2.5 segundos.

#### Scenario: Cópia confirmada
- **WHEN** o usuário copia dados com sucesso
- **THEN** a mensagem "✓ Dados copiados" DEVE aparecer por 2.5s

### Requirement: Double-click na lista de tickers
Ao dar duplo clique em um ticker na lista, o sistema DEVE aplicar o filtro para mostrar apenas aquele ticker.

#### Scenario: Duplo clique filtra
- **WHEN** o usuário dá duplo clique em "PETR4"
- **THEN** o filtro DEVE ser aplicado para mostrar apenas PETR4

### Requirement: Separação visual entre botões de ação
Os botões "Copiar Dados" e "Copiar Gráfico" DEVEM ter um padding interno de `ipadx=8, ipady=2` e um `ttk.Separator` entre eles.

#### Scenario: Botões com padding
- **WHEN** os botões são renderizados
- **THEN** eles DEVEM ter padding interno e um separador entre si
