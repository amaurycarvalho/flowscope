# Spec Delta — llm-chat-gui

## ADDED Requirements

### Requirement: Checkbox "Exibir fontes"

A aba "Chat AI" DEVE oferecer um checkbox "Exibir fontes" no cabeçalho, desmarcado por padrão e disponível também durante um envio. Alternar o checkbox DEVE re-renderizar a área de mensagens a partir da sessão, exibindo ou ocultando as fontes de todas as respostas do assistente, sem alterar a sessão nem o histórico enviado ao modelo.

#### Scenario: Estado inicial desmarcado
- **WHEN** a aba "Chat AI" é aberta
- **THEN** o checkbox "Exibir fontes" DEVE estar desmarcado e nenhuma fonte DEVE ser exibida

#### Scenario: Marcar exibe fontes anteriores
- **WHEN** o usuário marca "Exibir fontes" após uma ou mais respostas
- **THEN** todas as respostas do assistente com fontes DEVEM passar a exibir as suas respectivas fontes

#### Scenario: Desmarcar oculta fontes anteriores
- **WHEN** o usuário desmarca "Exibir fontes"
- **THEN** todas as respostas do assistente DEVEM deixar de exibir as fontes

#### Scenario: Alternar não altera a conversa
- **WHEN** o usuário alterna o checkbox
- **THEN** a sessão, o histórico e os tokens acumulados NÃO DEVEM ser alterados

### Requirement: Exibição das fontes separada da resposta

Com o checkbox marcado, as fontes consultadas DEVEM ser exibidas em bloco próprio imediatamente após a resposta do assistente, com separação visual clara do texto da resposta. Cada fonte DEVE exibir o caminho e, quando houver, o rótulo declarado. Com o checkbox desmarcado, nenhuma fonte DEVE ser exibida.

#### Scenario: Fontes em bloco separado
- **WHEN** o checkbox está marcado e a resposta possui fontes
- **THEN** as fontes DEVEM aparecer após a resposta, em bloco claramente separado do texto

#### Scenario: Resposta sem fontes
- **WHEN** o checkbox está marcado e a resposta não possui fontes
- **THEN** nenhum bloco de fontes DEVE ser exibido

#### Scenario: Rótulo exibido quando declarado
- **WHEN** uma fonte possui rótulo declarado pela LLM
- **THEN** o rótulo DEVE ser exibido junto do caminho correspondente

#### Scenario: Checkbox desmarcado não exibe fontes
- **WHEN** o checkbox está desmarcado
- **THEN** nenhuma lista de fontes DEVE integrar o corpo de qualquer resposta

## MODIFIED Requirements

### Requirement: Copiar chat e CSV

O sistema DEVE oferecer um botão "Copiar chat" na aba, que copia para a área de transferência exatamente o conteúdo exibido na área de mensagens, respeitando o estado do checkbox "Exibir fontes". A cópia de dados CSV DEVE incluir o mesmo conteúdo exibido do chat quando a aba "Chat AI" estiver ativa.

#### Scenario: Copiar chat
- **WHEN** o usuário clica em "Copiar chat"
- **THEN** o conteúdo exibido na área de mensagens DEVE ser copiado para a área de transferência

#### Scenario: Cópia segue o checkbox marcado
- **WHEN** o checkbox "Exibir fontes" está marcado e o usuário copia o chat
- **THEN** a cópia DEVE conter as fontes exibidas

#### Scenario: Cópia segue o checkbox desmarcado
- **WHEN** o checkbox "Exibir fontes" está desmarcado e o usuário copia o chat
- **THEN** a cópia NÃO DEVE conter as fontes

#### Scenario: CSV com chat ativo
- **WHEN** a aba "Chat AI" está ativa e o usuário aciona a cópia de dados
- **THEN** o conteúdo exibido do chat DEVE ser incluído na cópia, respeitando o checkbox
