## MODIFIED Requirements

### Requirement: --create-shortcut restrito ao Linux
O flag `--create-shortcut` DEVE funcionar apenas no Linux. Em outras plataformas, DEVE exibir mensagem informativa e encerrar sem erro (código de saída 0).

#### Scenario: --create-shortcut no Windows
- **WHEN** o usuário executa `flowscope --create-shortcut` no Windows
- **THEN** o sistema DEVE exibir "Funcionalidade disponível apenas no Linux." e encerrar com código de saída 0 (sem erro)

#### Scenario: --create-shortcut no macOS
- **WHEN** o usuário executa `flowscope --create-shortcut` no macOS
- **THEN** o sistema DEVE exibir "Funcionalidade disponível apenas no Linux." e encerrar com código de saída 0 (sem erro)
