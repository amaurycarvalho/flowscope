## ADDED Requirements

### Requirement: Exec com caminho absoluto

O sistema DEVE usar o caminho absoluto do executável no campo `Exec` do arquivo `.desktop`, resolvido via `Path(sys.argv[0]).resolve()`, e DEVE incluir a flag `--gui`.

#### Scenario: Exec contém caminho absoluto e --gui
- **WHEN** o usuário executa `flowscope --create-shortcut`
- **THEN** o campo `Exec` no `.desktop` DEVE conter o caminho absoluto do executável seguido de ` --gui`

### Requirement: Icon copiado para diretório permanente

O sistema DEVE copiar o ícone `flowscope.png` para `~/.local/share/icons/flowscope.png` (criando o diretório se necessário) e usar esse caminho permanente no campo `Icon` do `.desktop`. A resolução do ícone fonte DEVE funcionar tanto em modo desenvolvimento (via `__file__`) quanto em frozen build PyInstaller (via `sys._MEIPASS`).

#### Scenario: Icon resolvido e copiado no Linux
- **WHEN** o usuário executa `flowscope --create-shortcut` no Linux
- **THEN** o ícone DEVE ser copiado para `~/.local/share/icons/flowscope.png` e o campo `Icon` no `.desktop` DEVE apontar para esse arquivo

### Requirement: Atalho com StartupNotify

O sistema DEVE incluir `StartupNotify=true` no arquivo `.desktop` gerado.

#### Scenario: .desktop contém StartupNotify
- **WHEN** o usuário executa `flowscope --create-shortcut`
- **THEN** o arquivo `.desktop` gerado DEVE conter a linha `StartupNotify=true`
