## MODIFIED Requirements

### Requirement: Preferências persistentes
O sistema DEVE salvar e restaurar a última data selecionada, último gráfico, geometria da janela, a **largura do painel direito do divisor principal** (abas à esquerda / watch list e orientação à direita) e o último diretório dos diálogos de ticker em `~/.flowscope/config.json`. A largura do painel direito DEVE ser persistida como uma largura (não como a coordenada absoluta do divisor) e restaurada após a janela estar mapeada e no tamanho final, de modo que o painel direito mantenha a mesma largura mesmo quando a aplicação for reaberta em uma resolução diferente. O formato de posição absoluta do divisor DEVE ser descartado como base de restauração quando incompatível, e o divisor vertical sem sash (a estrutura de painel único) NÃO DEVE ser usado para salvar nem restaurar posição.

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

#### Scenario: Largura do painel direito salva no fechamento
- **WHEN** o usuário ajusta o divisor principal e fecha a aplicação
- **THEN** a largura do painel direito DEVE ser salva em `~/.flowscope/config.json`

#### Scenario: Largura do painel direito restaurada
- **WHEN** a aplicação inicia e há uma largura de painel direito salva
- **THEN** o divisor principal DEVE ser posicionado de modo que o painel direito fique com aquela largura

#### Scenario: Largura preservada em resolução maior
- **WHEN** a aplicação é fechada em uma resolução e reaberta em uma resolução maior
- **THEN** o painel direito DEVE manter a largura salva e o espaço adicional DEVE ser absorvido pelo painel esquerdo

#### Scenario: Largura preservada em resolução menor
- **WHEN** a aplicação é reaberta em uma resolução menor que a da sessão anterior
- **THEN** o painel direito DEVE manter a largura salva, limitada de modo que o painel esquerdo não colapse

#### Scenario: Posição absoluta legada descartada
- **WHEN** o arquivo de configuração contém uma posição absoluta de divisor no formato antigo
- **THEN** o sistema NÃO DEVE usá-la para restaurar o divisor e DEVE aplicar o posicionamento padrão
