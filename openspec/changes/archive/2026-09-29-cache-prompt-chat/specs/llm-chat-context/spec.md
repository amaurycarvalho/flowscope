## ADDED Requirements

### Requirement: Contexto estável com revalidação por assinatura

O bloco de contexto estável (conhecimento do FlowScope, fundamentos da watchlist e resumos de documentos) DEVE ser renderizado de forma determinística e associado a uma **assinatura de conteúdo**. Enquanto a assinatura não mudar, o bloco renderizado DEVE ser reusado byte-a-byte; quando a assinatura mudar, o bloco DEVE ser reconstruído. Fontes cuja composição depende da pergunta NÃO DEVEM integrar o bloco estável.

#### Scenario: Reuso enquanto a assinatura não muda

- **WHEN** uma nova pergunta é feita e a assinatura do contexto permanece a mesma
- **THEN** o bloco estável anterior DEVE ser reusado, sem recomputar o texto do prefixo

#### Scenario: Reconstrução quando o conteúdo muda

- **WHEN** os fundamentos, a watchlist ou o conjunto de resumos muda entre turnos
- **THEN** a assinatura DEVE mudar e o bloco estável DEVE ser reconstruído naquele turno

#### Scenario: Determinismo do bloco

- **WHEN** o bloco estável é reconstruído com as mesmas entradas
- **THEN** o texto resultante DEVE ser idêntico byte-a-byte ao anterior

#### Scenario: Fontes voláteis fora do bloco estável

- **WHEN** uma fonte adicional depende da pergunta
- **THEN** ela NÃO DEVE compor o bloco estável nem a assinatura, permanecendo no sufixo volátil
