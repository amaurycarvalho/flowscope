## ADDED Requirements

### Requirement: Leitura paginada de texto pesado

A operação `obter` DEVE aceitar os campos opcionais `offset` (inteiro maior ou igual a zero) e `limite` (inteiro maior que zero) para os nós de conteúdo pesado (texto integral de documentos/notícias). Sem os campos, DEVE devolver a página padrão a partir do início. Com os campos, DEVE devolver o trecho `[offset, offset+limite)` e informar na resposta o total de caracteres, o `offset` e o `limite` aplicados e se há continuação. Campo com tipo inválido DEVE devolver erro estruturado `tipo_invalido` com dica, sem encerrar o loop. O manifesto/playbook DEVEM orientar a paginações sucessivas quando o texto exceder o limite.

#### Scenario: Página intermediária
- **WHEN** a LLM emite `obter` com `offset` e `limite` válidos sobre um texto maior que o limite
- **THEN** o resultado DEVE conter o trecho correspondente e sinalizar o total e a existência de continuação

#### Scenario: Texto menor que a página
- **WHEN** o texto cabe dentro do `limite`
- **THEN** o resultado DEVE conter o texto inteiro e sinalizar que não há continuação

#### Scenario: Offset além do fim
- **WHEN** o `offset` é maior ou igual ao total do texto
- **THEN** o resultado DEVE ser vazio e sinalizar que não há continuação, sem erro

#### Scenario: Campo inválido
- **WHEN** `offset`/`limite` têm tipo ou valor inválidos (ex.: negativo, zero no limite)
- **THEN** o sistema DEVE devolver erro estruturado `tipo_invalido` com dica do tipo esperado

#### Scenario: Manifesto orienta a paginação
- **WHEN** o manifesto é montado
- **THEN** ele DEVE orientar a ler textos longos em páginas sucessivas via `obter` com `offset`/`limite`
