## Purpose

Fornece o widget de chat e a aba de topo "Chat AI" na interface gráfica, com os comportamentos de configuração, cópia, atalhos e tratamento de erro.

## ADDED Requirements

### Requirement: Widget ChatPanel reutilizável

O sistema DEVE fornecer um widget `ChatPanel(tkinter.Frame)` com área de mensagens com scroll, campo de entrada, botão "Enviar" e copy/paste livre. As respostas DEVEM ser exibidas em campo somente-leitura que permita seleção de texto, cursor visível e atalhos de teclado.

#### Scenario: ChatPanel sem escopo fixo
- **WHEN** `ChatPanel(root)` é criado
- **THEN** o painel DEVE consultar o contexto da watchlist completa, sem seletor de escopo

#### Scenario: Respostas somente-leitura com atalhos
- **WHEN** o usuário interage com o campo de respostas
- **THEN** a edição DEVE ser bloqueada, preservando cursor, seleção e Ctrl+A/C

### Requirement: Aba "Chat AI"

O sistema DEVE expor a aba de topo "Chat AI" na janela principal, entre "Análise do Ticker" e "Sobre", como ponto único de entrada do chat. A aba DEVE permanecer visível e a LLM DEVE inferir o ticker referido na pergunta, sem seletor de escopo.

#### Scenario: Aba posicionada e visível
- **WHEN** a janela principal é exibida
- **THEN** a aba "Chat AI" DEVE estar presente entre "Análise do Ticker" e "Sobre"

#### Scenario: Ticker inferido pela LLM
- **WHEN** o usuário pergunta sobre um ticker
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta, sem que a interface ofereça um seletor de escopo

### Requirement: Estado não configurado e botão "Configuração"

Quando `llm.chat.provider` está ausente ou é `none`, a aba "Chat AI" DEVE permanecer visível, com o campo de entrada desabilitado e exibindo orientação para configurar a LLM. O cabeçalho DEVE ter os botões "Copiar chat" e "Configuração", este último sempre visível logo após "Copiar chat" e abrindo o diálogo de configuração fornecido pela `llm-core`. Ao salvar a configuração, o estado DEVE ser reavaliado.

#### Scenario: Provedor não configurado
- **WHEN** `llm.chat.provider` está ausente ou é `none`
- **THEN** a aba DEVE exibir a orientação de configuração com a entrada desabilitada e o botão "Configuração" disponível

#### Scenario: Configuração salva
- **WHEN** o usuário salva uma configuração válida no diálogo
- **THEN** o campo de entrada DEVE ser habilitado

#### Scenario: Configuração sempre acessível
- **WHEN** a aba "Chat AI" está exibida
- **THEN** o botão "Configuração" DEVE estar visível no cabeçalho, logo após "Copiar chat"

### Requirement: Copiar chat e CSV

O sistema DEVE oferecer um botão "Copiar chat" na aba, que copia o conteúdo da sessão para a área de transferência. A cópia de dados CSV DEVE incluir o conteúdo do chat quando a aba "Chat AI" estiver ativa.

#### Scenario: Copiar chat
- **WHEN** o usuário clica em "Copiar chat"
- **THEN** o conteúdo da sessão DEVE ser copiado para a área de transferência

#### Scenario: CSV com chat ativo
- **WHEN** a aba "Chat AI" está ativa e o usuário aciona a cópia de dados
- **THEN** o conteúdo do chat DEVE ser incluído na cópia

### Requirement: Limpar conversa

O sistema DEVE oferecer um botão "Limpar" no cabeçalho, antes de "Copiar chat", que reinicia a sessão como se estivesse começando agora, limpando as mensagens exibidas e o histórico em memória. Antes de executar, o sistema DEVE pedir confirmação (Sim/Não) ao usuário; se o usuário recusar, a sessão NÃO DEVE ser alterada.

#### Scenario: Limpar confirmado
- **WHEN** o usuário clica em "Limpar" e confirma a operação
- **THEN** a sessão e a área de mensagens DEVEM ficar vazias, como uma conversa recém-iniciada

#### Scenario: Limpar cancelado
- **WHEN** o usuário clica em "Limpar" e recusa a confirmação
- **THEN** a conversa DEVE permanecer inalterada

#### Scenario: Posição do botão
- **WHEN** a aba "Chat AI" está exibida
- **THEN** o botão "Limpar" DEVE estar no cabeçalho, antes de "Copiar chat"

### Requirement: Tratamento de erros da LLM

Falhas da LLM durante o chat DEVEM ser exibidas na barra de status com mensagem amigável e registradas no log do sistema.

#### Scenario: Falha durante o chat
- **WHEN** a LLM fica ou está indisponível durante uma pergunta
- **THEN** a mensagem DEVE aparecer na barra de status e o erro DEVE ser registrado no log

### Requirement: Sessão não persistente

Cada abertura da aba DEVE começar com uma sessão limpa, sem persistência de histórico.

#### Scenario: Reabertura da aba
- **WHEN** a aba "Chat AI" é reaberta
- **THEN** a sessão DEVE iniciar vazia, sem mensagens anteriores
