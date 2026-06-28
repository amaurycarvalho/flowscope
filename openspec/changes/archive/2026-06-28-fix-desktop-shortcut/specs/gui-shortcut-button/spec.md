## ADDED Requirements

### Requirement: Botão "Criar atalho no desktop" na GUI

O sistema DEVE exibir um botão "Criar atalho no desktop" na barra superior da GUI, ao lado do botão "Copiar Dados", visível apenas quando todas as condições forem satisfeitas: (1) sistema operacional Linux, (2) atalho `flowscope.desktop` não existe em `~/Desktop/` nem em `~/Área de Trabalho/`.

#### Scenario: Botão visível no Linux sem atalho
- **WHEN** o sistema é Linux e não existe `~/Desktop/flowscope.desktop` nem `~/Área de Trabalho/flowscope.desktop`
- **THEN** o botão "Criar atalho no desktop" DEVE estar visível na barra superior

#### Scenario: Botão oculto no Linux com atalho existente
- **WHEN** o sistema é Linux e `~/Desktop/flowscope.desktop` existe
- **THEN** o botão "Criar atalho no desktop" NÃO DEVE estar visível

#### Scenario: Botão oculto no Windows/macOS
- **WHEN** o sistema é Windows ou macOS
- **THEN** o botão "Criar atalho no desktop" NÃO DEVE estar visível

### Requirement: Criação do atalho via botão

Ao clicar no botão "Criar atalho no desktop", o sistema DEVE executar a mesma lógica de criação de atalho usada pelo CLI (`--create-shortcut`). Em caso de sucesso, DEVE exibir "Atalho criado!" na barra de status e tornar o botão imediatamente invisível.

#### Scenario: Clique no botão cria atalho com sucesso
- **WHEN** o usuário clica no botão "Criar atalho no desktop"
- **THEN** o sistema DEVE criar o arquivo `~/Desktop/flowscope.desktop`, exibir "Atalho criado!" na barra de status, e ocultar o botão

#### Scenario: Falha na criação exibe erro na barra de status
- **WHEN** o usuário clica no botão e a criação do atalho falha (ex: permissão negada)
- **THEN** o sistema DEVE exibir a mensagem de erro na barra de status e manter o botão visível
