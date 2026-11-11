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

Com o checkbox marcado, as fontes consultadas DEVEM ser exibidas em bloco próprio imediatamente após a resposta do assistente, com separação visual clara do texto da resposta. O bloco DEVE ser introduzido pelo rótulo `Fontes consultadas:`, com uma linha em branco antes e quebra de linha depois. Cada fonte DEVE exibir o caminho e, quando houver, o rótulo declarado. Com o checkbox desmarcado, nenhuma fonte DEVE ser exibida.

#### Scenario: Fontes em bloco separado
- **WHEN** o checkbox está marcado e a resposta possui fontes
- **THEN** as fontes DEVEM aparecer após a resposta, em bloco claramente separado do texto, precedidas de `Fontes consultadas:`

#### Scenario: Resposta sem fontes
- **WHEN** o checkbox está marcado e a resposta não possui fontes
- **THEN** nenhum bloco de fontes DEVE ser exibido

#### Scenario: Rótulo exibido quando declarado
- **WHEN** uma fonte possui rótulo declarado pela LLM
- **THEN** o rótulo DEVE ser exibido junto do caminho correspondente

#### Scenario: Checkbox desmarcado não exibe fontes
- **WHEN** o checkbox está desmarcado
- **THEN** nenhuma lista de fontes DEVE integrar o corpo de qualquer resposta

### Requirement: Marcações exibidas em negrito

As marcações de exibição `Você:`, `Assistente:` e `Fontes consultadas:` DEVEM ser exibidas em negrito no campo de mensagens, sem alterar o texto simples usado pela cópia de CSV.

#### Scenario: Marcações em negrito
- **WHEN** a conversa é renderizada
- **THEN** `Você:`, `Assistente:` e, quando aplicável, `Fontes consultadas:` DEVEM aparecer em negrito

#### Scenario: Texto simples preservado
- **WHEN** o conteúdo é lido como texto simples para o CSV
- **THEN** as marcações DEVEM estar presentes sem a formatação de negrito

## MODIFIED Requirements

### Requirement: Copiar chat e CSV

O sistema DEVE oferecer um botão "Copiar chat" na aba, que copia para a área de transferência o conteúdo exibido na área de mensagens convertido para Markdown (`Você:`, `Assistente:` e `Fontes consultadas:` entre `**`), respeitando o estado do checkbox "Exibir fontes". A cópia de dados CSV DEVE incluir o conteúdo exibido do chat em texto simples quando a aba "Chat AI" estiver ativa.

#### Scenario: Copiar chat em Markdown
- **WHEN** o usuário clica em "Copiar chat"
- **THEN** o conteúdo exibido na área de mensagens DEVE ser copiado para a área de transferência com as marcações em negrito convertidas para `**...**`

#### Scenario: Cópia segue o checkbox marcado
- **WHEN** o checkbox "Exibir fontes" está marcado e o usuário copia o chat
- **THEN** a cópia DEVE conter as fontes exibidas

#### Scenario: Cópia segue o checkbox desmarcado
- **WHEN** o checkbox "Exibir fontes" está desmarcado e o usuário copia o chat
- **THEN** a cópia NÃO DEVE conter as fontes

#### Scenario: CSV com chat ativo
- **WHEN** a aba "Chat AI" está ativa e o usuário aciona a cópia de dados
- **THEN** o conteúdo exibido do chat DEVE ser incluído na cópia em texto simples, respeitando o checkbox
