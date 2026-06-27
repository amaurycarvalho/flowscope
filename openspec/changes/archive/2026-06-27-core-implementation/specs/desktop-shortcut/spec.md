## ADDED Requirements

### Requirement: Criação de atalho .desktop no Linux
O sistema DEVE criar um arquivo `.desktop` no diretório Desktop do usuário Linux quando o flag `--create-shortcut` é utilizado.

#### Scenario: Criação de atalho no diretório Desktop
- **WHEN** o usuário executa `flowscope --create-shortcut` no Linux
- **THEN** um arquivo `flowscope.desktop` DEVE ser criado em `~/Desktop/` (ou `~/Área de Trabalho/`), contendo as entradas `Name=FlowScope`, `Exec=<caminho do executável>`, `Type=Application`, `Terminal=false`, e apontando para o ícone `flowscope.png`

#### Scenario: Atalho já existe
- **WHEN** o arquivo `flowscope.desktop` já existe no Desktop
- **THEN** o sistema DEVE sobrescrever o arquivo existente com as novas configurações

#### Scenario: Criação de atalho falha por falta de permissão
- **WHEN** o diretório Desktop não pode ser escrito
- **THEN** o sistema DEVE exibir mensagem de erro informando o problema de permissão

### Requirement: --create-shortcut restrito ao Linux
O flag `--create-shortcut` DEVE funcionar apenas no Linux. Em outras plataformas, DEVE informar que a funcionalidade não está disponível.

#### Scenario: --create-shortcut no Windows
- **WHEN** o usuário executa `flowscope --create-shortcut` no Windows
- **THEN** o sistema DEVE exibir "Funcionalidade disponível apenas no Linux." e encerrar sem erro

#### Scenario: --create-shortcut no macOS
- **WHEN** o usuário executa `flowscope --create-shortcut` no macOS
- **THEN** o sistema DEVE exibir "Funcionalidade disponível apenas no Linux." e encerrar sem erro
