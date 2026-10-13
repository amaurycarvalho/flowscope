## MODIFIED Requirements

### Requirement: Acesso ao log da aplicação

A aba "Sobre" DEVE exibir um botão que abre o diretório de logs
`~/.flowscope/logs` no aplicativo padrão do sistema. Quando o diretório ainda
não existir, o sistema DEVE informar a indisponibilidade na barra de status, sem
falhar silenciosamente.

#### Scenario: Log existente é aberto

- **WHEN** o usuário aciona o botão do log e o diretório de logs existe
- **THEN** o aplicativo padrão DEVE abrir o diretório `~/.flowscope/logs`

#### Scenario: Log inexistente informa indisponibilidade

- **WHEN** o usuário aciona o botão do log e o diretório de logs não existe
- **THEN** a barra de status DEVE informar que o log ainda não está disponível
