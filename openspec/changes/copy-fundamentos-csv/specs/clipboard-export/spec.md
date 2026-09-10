## ADDED Requirements

### Requirement: Cópia dos dados da tabela de Fundamentos

O sistema DEVE, quando a aba principal "Análise Geral" e a sub-aba "Fundamentos" estiverem selecionadas, copiar o conteúdo da tabela de Fundamentos — uma linha de cabeçalho com os rótulos das colunas exibidas e uma linha por ticker apresentado, com os valores formatados como na tabela — em vez do CSV bruto de negociações.

A cópia DEVE usar separador de campo `;` (ponto-e-vírgula), preservar a ordem dos tickers exibida na tabela e reutilizar o mesmo mecanismo de clipboard do fluxo existente (`pyxclip` como primário e fallback para o clipboard do Tkinter).

#### Scenario: Fundamentos selecionada copia a tabela

- **WHEN** o usuário está na aba "Análise Geral" com a sub-aba "Fundamentos" selecionada e aciona "Copiar Dados" (botão ou `Ctrl+Shift+C`)
- **THEN** o sistema DEVE copiar o cabeçalho das colunas da tabela e uma linha por ticker exibido, com os valores formatados, em vez do CSV bruto de negociações

#### Scenario: Cabeçalho e ordem dos tickers

- **WHEN** a tabela de Fundamentos é copiada
- **THEN** a primeira linha copiada DEVE conter os rótulos das colunas exibidas e as linhas seguintes DEVEM seguir a mesma ordem de tickers da tabela

#### Scenario: Outra sub-aba mantém o fluxo existente

- **WHEN** o usuário está na aba "Análise Geral" com uma sub-aba diferente de "Fundamentos" e aciona "Copiar Dados"
- **THEN** o sistema DEVE copiar o CSV bruto de negociações conforme o fluxo existente

#### Scenario: Análise do Ticker mantém o fluxo existente

- **WHEN** o usuário está na aba "Análise do Ticker" e aciona "Copiar Dados"
- **THEN** o sistema DEVE copiar o CSV bruto do ticker selecionado conforme o fluxo existente

#### Scenario: Tabela de Fundamentos vazia

- **WHEN** a sub-aba "Fundamentos" está selecionada e não há linhas para copiar
- **THEN** o sistema NÃO DEVE copiar conteúdo e DEVE exibir a mensagem "Nenhum ticker disponível para cópia." na barra de status

#### Scenario: Fallback do clipboard

- **WHEN** `pyxclip` não está disponível e a tabela de Fundamentos é copiada
- **THEN** o sistema DEVE usar o clipboard do Tkinter e exibir o feedback de fallback do fluxo existente
