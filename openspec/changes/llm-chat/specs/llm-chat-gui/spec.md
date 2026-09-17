## ADDED Requirements

### Requirement: Widget ChatPanel reutilizável
Widget `ChatPanel(tkinter.Frame)` parametrizado por `ticker: str | None`. Área de mensagens com scroll, campo de entrada, botão Enviar, copy/paste livre.

#### Scenario: ChatPanel sem ticker (Chat Geral)
- **WHEN** `ChatPanel(root, ticker=None)` é criado
- **THEN** a busca no VectorStore DEVE ocorrer sem filtro de ticker

#### Scenario: ChatPanel com ticker (Chat Ticker)
- **WHEN** `ChatPanel(root, ticker="ALZR11")` é criado
- **THEN** a busca no VectorStore DEVE filtrar `WHERE ticker = "ALZR11"`

### Requirement: Estado "Chat desabilitado"
Quando `chat.provider` não está configurado, o sistema DEVE exibir uma mensagem com botão "Configurar".

#### Scenario: Provedor não configurado
- **WHEN** `chat.provider` está ausente na configuração
- **THEN** o painel DEVE exibir a mensagem de chat desabilitado com o botão "Configurar"

### Requirement: Estado "Sem documentos"
Quando o VectorStore está vazio para o ticker, o sistema DEVE exibir o botão "Atualizar Documentos" com barra de progresso.

#### Scenario: VectorStore vazio
- **WHEN** não há documentos indexados para o ticker
- **THEN** o painel DEVE exibir o botão "Atualizar Documentos" com barra de progresso

### Requirement: Aba "Chat Geral" na Análise Geral
O sistema DEVE expor `ChatPanel(ticker=None)` na Análise Geral, visível apenas com `chat.provider` configurado.

#### Scenario: Chat Geral visível
- **WHEN** `chat.provider` está configurado
- **THEN** a aba "Chat Geral" DEVE estar visível com `ChatPanel(ticker=None)`

### Requirement: Aba "Chat Ticker" na Análise do Ticker
O sistema DEVE expor `ChatPanel(ticker=<selecionado>)` na Análise do Ticker, atualizando ao trocar o ticker.

#### Scenario: Troca de ticker
- **WHEN** o ticker selecionado muda
- **THEN** o `ChatPanel` da aba "Chat Ticker" DEVE passar a filtrar pelo novo ticker

### Requirement: ConfigDialog
O sistema DEVE oferecer um `ConfigDialog` com dropdown de provedor com presets, API Key, modelo e botão Testar Conexão, com configuração separada para embedding e chat.

#### Scenario: Abrir e salvar configuração
- **WHEN** o usuário seleciona um preset, informa a API Key e salva
- **THEN** a configuração DEVE ser persistida e o chat DEVE passar a ficar disponível

### Requirement: Sessão não persistente
Cada aba DEVE começar com uma sessão limpa, sem persistência de histórico, com copy/paste livre.

#### Scenario: Reabertura da aba
- **WHEN** a aba de chat é reaberta
- **THEN** a sessão DEVE iniciar vazia, sem mensagens anteriores
