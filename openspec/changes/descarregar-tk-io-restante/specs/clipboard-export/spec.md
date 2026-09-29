## MODIFIED Requirements

### Requirement: Cópia de gráfico como imagem PNG para clipboard

O sistema DEVE copiar o gráfico matplotlib atual como imagem PNG para o clipboard. O botão "Copiar Gráfico" está localizado no toolbar nativo do chart (`ToolbarBR`), disponível para qualquer chart que utilize o toolbar.

O rendering da figura em PNG DEVE permanecer serializado com a thread da interface, mas a transferência da imagem ao clipboard do sistema DEVE ocorrer fora da thread da interface, mantendo-a responsiva. O feedback de sucesso ou erro DEVE ser exibido na barra de status na thread do Tk, e o estado ocupado dos controles DEVE ser governado pela autoridade única de estado enquanto a cópia estiver em andamento.

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

#### Scenario: Interface responsiva durante a cópia
- **WHEN** a transferência ao clipboard demora (ex: `xclip` lento ou figura grande)
- **THEN** a thread da interface NÃO DEVE aguardar a conclusão do comando de clipboard e DEVE permanecer responsiva

#### Scenario: Estado ocupado durante a transferência
- **WHEN** a transferência ao clipboard está em andamento
- **THEN** a autoridade única de estado DEVE entrar em ocupado ao iniciar e sair ao concluir, restaurando controles e cursor
