## MODIFIED Requirements

### Requirement: Cópia de gráfico como imagem PNG para clipboard
O sistema DEVE copiar o gráfico matplotlib atual como imagem PNG para o clipboard. O botão "Copiar Gráfico" está localizado no toolbar nativo do chart (`ToolbarBR`), disponível para qualquer chart que utilize o toolbar.

#### Scenario: Copiar gráfico para clipboard no Linux
- **WHEN** o usuário clica em "Copiar Gráfico" no toolbar do chart no Linux
- **THEN** o sistema DEVE salvar a figura como PNG temporário e usar `xclip -selection clipboard -t image/png -i` para transferir ao clipboard

#### Scenario: Copiar gráfico para clipboard no Windows
- **WHEN** o usuário clica em "Copiar Gráfico" no toolbar do chart no Windows
- **THEN** o sistema DEVE usar ctypes com `win32clipboard` (via `PIL.ImageGrab` ou API direta) para transferir a imagem PNG ao clipboard

#### Scenario: Copiar gráfico para clipboard no macOS
- **WHEN** o usuário clica em "Copiar Gráfico" no toolbar do chart no macOS
- **THEN** o sistema DEVE usar `osascript` ou `pbcopy` com dados PNG codificados para transferir ao clipboard

#### Scenario: Falha na cópia de imagem
- **WHEN** o comando nativo de clipboard falha (ex: `xclip` não instalado no Linux)
- **THEN** o sistema DEVE exibir mensagem de erro descritiva na barra de status da GUI informando o comando faltante

#### Scenario: Cópia de gráfico bem-sucedida com feedback na statusbar
- **WHEN** o gráfico é copiado com sucesso
- **THEN** a barra de status DEVE exibir "Gráfico copiado para a área de transferência."
