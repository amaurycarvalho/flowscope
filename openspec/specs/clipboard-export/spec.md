## ADDED Requirements

### Requirement: Cópia de dados CSV para clipboard
O sistema DEVE copiar os dados brutos do CSV original (SgmtNm=CASH) formatados como CSV para o clipboard do sistema operacional. Os campos copiados DEVERÃO ser: `RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol`.

A cópia DEVE usar `pyxclip` como mecanismo primário, com fallback para o clipboard nativo do Tkinter.

O formato DEVE usar separador de campo `;` (ponto-e-vírgula) e separador decimal `,` (vírgula) — padrão brasileiro.

#### Scenario: Copiar CSV bruto de todos os tickers selecionados na Análise Geral
- **WHEN** o usuário está na aba "Análise Geral" com múltiplos tickers selecionados e clica no botão "Copiar Dados" (ou `Ctrl+Shift+C`)
- **THEN** o sistema DEVE copiar linhas CSV com os campos `RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol` para cada ticker selecionado, com cabeçalho na primeira linha

#### Scenario: Copiar CSV bruto de um ticker na Análise do Ticker
- **WHEN** o usuário está na aba "Análise do Ticker" e clica no botão "Copiar Dados" (ou `Ctrl+Shift+C`)
- **THEN** o sistema DEVE copiar linhas CSV apenas do ticker selecionado para visualização no painel

#### Scenario: Fallback Tkinter quando pyxclip não está disponível
- **WHEN** `pyxclip` não está instalado e o usuário solicita cópia
- **THEN** o sistema DEVE usar `self.clipboard_clear()` + `self.clipboard_append()` e exibir mensagem na barra de status indicando fallback

#### Scenario: Botão desabilitado durante carregamento
- **WHEN** o sistema está baixando/processando dados
- **THEN** o botão "Copiar Dados" DEVE estar desabilitado, junto com os demais controles da interface

#### Scenario: Botão habilitado após dados carregados
- **WHEN** o carregamento de dados é concluído com sucesso
- **THEN** o botão "Copiar Dados" DEVE ser habilitado

#### Scenario: Cópia bem-sucedida com feedback na statusbar
- **WHEN** os dados CSV são copiados para o clipboard com sucesso
- **THEN** a barra de status DEVE exibir "Dados copiados!"

#### Scenario: Nenhum ticker selecionado na Análise Geral
- **WHEN** o usuário está na aba "Análise Geral" com nenhum ticker selecionado e clica em "Copiar Dados"
- **THEN** o sistema DEVE usar o ticker selecionado para visualização (primeiro da lista) como fallback

#### Scenario: Formato decimal brasileiro no CSV
- **WHEN** o sistema gera o CSV
- **THEN** valores decimais DEVEM usar `,` como separador decimal (ex: `37,50` em vez de `37.50`)

### Requirement: Cópia de gráfico como imagem PNG para clipboard
O sistema DEVE copiar o gráfico matplotlib atual como imagem PNG para o clipboard. O botão "Copiar Gráfico" está localizado no toolbar nativo do chart (`ToolbarBR`), disponível para qualquer chart que utilize o toolbar.

#### Scenario: Copiar gráfico para clipboard no Linux
- **WHEN** o usuário solicita cópia do gráfico no Linux
- **THEN** o sistema DEVE salvar a figura como PNG temporário e usar `xclip -selection clipboard -t image/png -i` para transferir ao clipboard

#### Scenario: Copiar gráfico para clipboard no Windows
- **WHEN** o usuário solicita cópia do gráfico no Windows
- **THEN** o sistema DEVE usar ctypes com `win32clipboard` (via `PIL.ImageGrab` ou API direta) para transferir a imagem PNG ao clipboard

#### Scenario: Copiar gráfico para clipboard no macOS
- **WHEN** o usuário solicita cópia do gráfico no macOS
- **THEN** o sistema DEVE usar `osascript` ou `pbcopy` com dados PNG codificados para transferir ao clipboard

#### Scenario: Falha na cópia de imagem
- **WHEN** o comando nativo de clipboard falha (ex: `xclip` não instalado no Linux)
- **THEN** o sistema DEVE exibir mensagem de erro descritiva na barra de status da GUI informando o comando faltante

#### Scenario: Cópia de gráfico bem-sucedida com feedback na statusbar
- **WHEN** o gráfico é copiado com sucesso
- **THEN** a barra de status DEVE exibir "Gráfico copiado para a área de transferência."

### Requirement: Segmento e quantidade de trades propagados no daily_data
O sistema DEVE incluir os campos `segment` (SgmtNm) e `trades_qty` (TradQty) no dicionário `daily_data` retornado pelo `AnalyzeTickersUseCase.execute()`.

#### Scenario: daily_data contém segment e trades_qty
- **WHEN** o `AnalyzeTickersUseCase` constrói o dicionário resultado
- **THEN** cada registro em `daily_data` DEVE conter as chaves `"segment"` (str) e `"trades_qty"` (int)

### Requirement: CSV contém todas as datas de amostragem
O CSV DEVE incluir todas as datas de amostragem, independentemente de o ticker específico ter negociado ou não naquela data. Datas sem trades DEVEM aparecer como `RptDt;TckrSymb;;;;;;;` (valores vazios).

A lista completa de datas de amostragem DEVE ser propagada do use case até a GUI via chave `_sampling_dates` no dict resultado, extraída em `set_current_data()` e armazenada em `self._sampling_dates`.

#### Scenario: Data sem trade do ticker aparece vazia no CSV
- **WHEN** um ticker não negociou em uma data de amostragem
- **THEN** o CSV DEVE conter a linha `{data};{ticker};;;;;;;` com valores vazios

#### Scenario: Todas as datas de amostragem no CSV
- **WHEN** o CSV é gerado
- **THEN** o CSV DEVE conter exatamente N linhas por ticker, onde N é o número de datas de amostragem (incluindo datas sem trade)

### Requirement: Cópia de gráfico como imagem PNG para clipboard
O sistema DEVE copiar o gráfico matplotlib atual como imagem PNG para o clipboard. O botão "Copiar Gráfico" está localizado no toolbar nativo do chart (`ToolbarBR`), disponível para qualquer chart que utilize o toolbar.

#### Scenario: Copiar gráfico para clipboard no Linux
- **WHEN** o usuário solicita cópia do gráfico no Linux
- **THEN** o sistema DEVE salvar a figura como PNG temporário e usar `xclip -selection clipboard -t image/png -i` para transferir ao clipboard

#### Scenario: Copiar gráfico para clipboard no Windows
- **WHEN** o usuário solicita cópia do gráfico no Windows
- **THEN** o sistema DEVE usar ctypes com `win32clipboard` (via `PIL.ImageGrab` ou API direta) para transferir a imagem PNG ao clipboard

#### Scenario: Copiar gráfico para clipboard no macOS
- **WHEN** o usuário solicita cópia do gráfico no macOS
- **THEN** o sistema DEVE usar `osascript` ou `pbcopy` com dados PNG codificados para transferir ao clipboard

#### Scenario: Falha na cópia de imagem
- **WHEN** o comando nativo de clipboard falha (ex: `xclip` não instalado no Linux)
- **THEN** o sistema DEVE exibir mensagem de erro descritiva na barra de status da GUI informando o comando faltante

#### Scenario: Cópia de gráfico bem-sucedida com feedback na statusbar
- **WHEN** o gráfico é copiado com sucesso
- **THEN** a barra de status DEVE exibir "Gráfico copiado para a área de transferência."
