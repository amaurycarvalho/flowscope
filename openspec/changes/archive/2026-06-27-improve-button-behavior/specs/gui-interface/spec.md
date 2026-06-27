## ADDED Requirements

### Requirement: Botão "Hoje" carrega dados automaticamente

O sistema DEVE, ao clicar no botão "Hoje", atualizar o DateEntry para a data atual E executar imediatamente o carregamento de dados (mesma ação do botão "Carregar"), como se o usuário tivesse clicado em "Carregar" em sequência.

#### Scenario: Clique no botão Hoje carrega dados do dia
- **WHEN** o usuário clica no botão "Hoje"
- **THEN** o DateEntry DEVE ser atualizado para a data atual E os dados DEVEM ser carregados para essa data, com o mesmo comportamento (loading state, statusbar, gráficos) do botão "Carregar"
