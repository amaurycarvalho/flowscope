## ADDED Requirements

### Requirement: Widget ChatPanel reutilizável
Widget `ChatPanel(tkinter.Frame)` parametrizado por `ticker: str | None`. Área de mensagens com scroll, campo de entrada, botão Enviar, copy/paste livre.

#### Scenario: ChatPanel sem ticker (Chat Geral)
- **WHEN** `ChatPanel(root, ticker=None)` — busca sem filtro no VectorStore

#### Scenario: ChatPanel com ticker (Chat Ticker)
- **WHEN** `ChatPanel(root, ticker="ALZR11")` — filtra `WHERE ticker = "ALZR11"`

### Requirement: Estado "Chat desabilitado"
Quando `chat.provider` não configurado, exibir mensagem com botão "Configurar".

### Requirement: Estado "Sem documentos"
Quando VectorStore vazio para o ticker, exibir botão "Atualizar Documentos" com barra de progresso.

### Requirement: Aba "Chat Geral" na Análise Geral
`ChatPanel(ticker=None)` na Análise Geral. Visível apenas com `chat.provider` configurado.

### Requirement: Aba "Chat Ticker" na Análise do Ticker
`ChatPanel(ticker=<selecionado>)` na Análise do Ticker. Atualiza ao trocar ticker.

### Requirement: ConfigDialog
Dropdown de provedor com presets, API Key, modelo, botão Testar Conexão. Configuração separada para embedding e chat.

### Requirement: Sessão não persistente
Cada aba começa limpa. Sem persistência de histórico. Copy/paste livre.
