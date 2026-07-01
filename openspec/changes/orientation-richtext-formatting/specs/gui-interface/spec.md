## MODIFIED Requirements

### Requirement: OrientationPanel para conteúdo explicativo
O sistema DEVE exibir um OrientationPanel na barra lateral direita contendo título e texto explicativo fixo associado à sub-aba ativa. Cada sub-aba DEVE ter seu próprio conteúdo explicativo composto por (objetivo, pergunta respondida, indicadores envolvidos, como interpretá-lo), nesta ordem. O texto explicativo DEVE suportar formatação rica nativa: cabeçalhos de seção (Objetivo, Responde a pergunta, Indicadores envolvidos, Como interpretar) em **negrito** e perguntas em itálico. O método `set_content(title, body)` DEVE aceitar `body` como uma lista de tuplas `(str, str)` onde o segundo elemento é o nome da tag de formatação.

#### Scenario: OrientationPanel exibe texto com formatação
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o OrientationPanel DEVE exibir "Objetivo:" em **negrito**, a pergunta em itálico, e os demais textos sem formatação especial

#### Scenario: set_content aceita lista de tuplas
- **WHEN** o sistema chama `set_content("Título", [("Objetivo: ", "bold"), ("texto plano", "")])`
- **THEN** o OrientationPanel DEVE exibir "Objetivo:" em negrito e "texto plano" sem formatação

## ADDED Requirements

### Requirement: Formatação via tags tk.Text
O OrientationPanel DEVE configurar duas tags no widget `tk.Text`: `"bold"` (fonte TkDefaultFont 9 bold) e `"italic"` (fonte TkDefaultFont 9 italic). Tags DEVEM ser aplicadas conforme o nome da tag em cada tupla do body.

#### Scenario: Tag bold aplicada a cabeçalhos
- **WHEN** o body contém `("Objetivo: ", "bold")`
- **THEN** o texto "Objetivo:" DEVE ser exibido em negrito

#### Scenario: Tag italic aplicada a perguntas
- **WHEN** o body contém `("pergunta", "italic")`
- **THEN** o texto "pergunta" DEVE ser exibido em itálico

#### Scenario: Tag vazia não aplica formatação
- **WHEN** o body contém `("texto plano", "")`
- **THEN** o texto DEVE ser exibido sem formatação especial
