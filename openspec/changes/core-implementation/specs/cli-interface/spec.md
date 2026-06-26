## ADDED Requirements

### Requirement: Ponto de entrada via argparse
O sistema DEVE fornecer uma interface de linha de comando usando argparse com os flags `--gui`, `--tickers`, `--vwap`, `--cvd`, `--help`, `--version`, `--create-shortcut`.

#### Scenario: Execução sem argumentos
- **WHEN** o usuário executa `flowscope` sem argumentos
- **THEN** o sistema DEVE baixar dados da data de referência padrão (hoje), calcular indicadores para os 15 tickers padrão e exibir resultados no terminal

#### Scenario: Flag --help
- **WHEN** o usuário executa `flowscope --help`
- **THEN** o sistema DEVE exibir a lista de todos os flags com descrições em português

#### Scenario: Flag --version
- **WHEN** o usuário executa `flowscope --version`
- **THEN** o sistema DEVE exibir o número da versão conforme definido em `pyproject.toml`

### Requirement: Exportação CSV de VWAP via --vwap
O sistema DEVE exportar os valores de VWAP dos tickers selecionados em formato CSV quando a flag `--vwap` é utilizada.

#### Scenario: Exportação VWAP para arquivo
- **WHEN** o usuário executa `flowscope --vwap`
- **THEN** um arquivo CSV DEVE ser gerado com colunas: Ticker, VWAP_Periodo, e VWAPs diários (uma coluna por data da janela)

#### Scenario: Exportação VWAP com tickers específicos
- **WHEN** o usuário executa `flowscope --vwap --tickers meus_tickers.txt`
- **THEN** o CSV gerado DEVE conter apenas os tickers listados no arquivo

### Requirement: Exportação CSV de CVD via --cvd
O sistema DEVE exportar os valores de CVD dos tickers selecionados em formato CSV quando a flag `--cvd` é utilizada.

#### Scenario: Exportação CVD para arquivo
- **WHEN** o usuário executa `flowscope --cvd`
- **THEN** um arquivo CSV DEVE ser gerado com colunas: Ticker, CVD_Acumulado, e CVDs diários (uma coluna por data da janela)

### Requirement: Seleção de tickers via arquivo texto
O sistema DEVE aceitar um arquivo texto com lista de tickers (um por linha) via flag `--tickers`.

#### Scenario: Arquivo de tickers válido
- **WHEN** o usuário executa `flowscope --tickers lista.txt` e o arquivo contém "PETR4\nVALE3\nITUB4"
- **THEN** o sistema DEVE processar apenas os tickers PETR4, VALE3, ITUB4

#### Scenario: Arquivo de tickers não encontrado
- **WHEN** o usuário executa `flowscope --tickers arquivo_inexistente.txt`
- **THEN** o sistema DEVE exibir mensagem de erro em português e encerrar com código de erro

### Requirement: Abertura da GUI via --gui
O sistema DEVE abrir a interface gráfica quando a flag `--gui` é utilizada.

#### Scenario: Flag --gui
- **WHEN** o usuário executa `flowscope --gui`
- **THEN** a janela Tkinter DEVE ser aberta com todos os widgets e gráficos da GUI

### Requirement: Criação de atalho desktop via --create-shortcut
O sistema DEVE criar um atalho `.desktop` no diretório Desktop do usuário Linux quando a flag `--create-shortcut` é utilizada.

#### Scenario: Criação de atalho no Linux
- **WHEN** o usuário executa `flowscope --create-shortcut` no Linux
- **THEN** um arquivo `flowscope.desktop` DEVE ser criado em `~/Desktop/` (ou `~/Área de Trabalho/`) apontando para o executável

#### Scenario: --create-shortcut em plataforma não-Linux
- **WHEN** o usuário executa `flowscope --create-shortcut` no Windows ou macOS
- **THEN** o sistema DEVE exibir mensagem informando que esta funcionalidade está disponível apenas no Linux
