## ADDED Requirements

### Requirement: Cópia de dados CSV para clipboard
O sistema DEVE copiar os dados dos indicadores formatados como CSV para o clipboard do sistema operacional usando pyxclip.

#### Scenario: Copiar CSV para clipboard no Linux
- **WHEN** o usuário solicita cópia de dados no Linux
- **THEN** pyxclip DEVE transferir o texto CSV para o clipboard via `xclip`

#### Scenario: Copiar CSV para clipboard no Windows
- **WHEN** o usuário solicita cópia de dados no Windows
- **THEN** pyxclip DEVE transferir o texto CSV para o clipboard do Windows

#### Scenario: Copiar CSV para clipboard no macOS
- **WHEN** o usuário solicita cópia de dados no macOS
- **THEN** pyxclip DEVE transferir o texto CSV para o clipboard via `pbcopy`

### Requirement: Cópia de gráfico como imagem PNG para clipboard
O sistema DEVE copiar o gráfico matplotlib atual como imagem PNG para o clipboard usando ctypes e comandos nativos da plataforma.

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
- **THEN** o sistema DEVE exibir mensagem de erro descritiva informando o comando faltante
