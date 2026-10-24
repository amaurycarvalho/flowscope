## ADDED Requirements

### Requirement: Manifesto anuncia os caminhos de direitos e obrigações

Quando o ramo `/direitos-obrigacoes` existir na árvore corrente, o manifesto e o playbook DEVEM anunciar os caminhos canônicos aninhados aplicáveis:

- `/direitos-obrigacoes/data-referencia`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/<id>/geral`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/<id>/adicionais`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/<id>/ltv`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/<id>/documentos`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/agregado/resumo`;
- `/direitos-obrigacoes/<obrigacoes|direitos>/titulos/<tipo>/sem-fonte`.

O manifesto DEVE anunciar apenas os tipos e caminhos efetivamente presentes na árvore corrente, omitindo caminhos de tipos ausentes. O playbook DEVE orientar a LLM a navegar por esses caminhos para responder sobre títulos emitidos, títulos mantidos, LTV, garantias, situação e documentos relacionados.

A árvore DEVE ser montada exclusivamente a partir do cache normalizado por ticker, sem baixar, extrair, resumir ou consultar a CVM/B3 durante a conversa. Um nó `sem-fonte` DEVE ser uma folha com conteúdo explicativo, não um nó interno vazio.

#### Scenario: Caminhos de obrigações no manifesto
- **WHEN** o ticker possui obrigações de renda fixa em cache
- **THEN** o manifesto DEVE anunciar os caminhos de `/direitos-obrigacoes/obrigacoes/titulos/<tipo>/<id>/...` presentes

#### Scenario: Caminhos de direitos no manifesto
- **WHEN** o ticker possui direitos de renda fixa em cache
- **THEN** o manifesto DEVE anunciar os caminhos de `/direitos-obrigacoes/direitos/titulos/<tipo>/<id>/...` presentes

#### Scenario: Agregado e ausência de fonte anunciados
- **WHEN** o tipo possui apenas agregado ou ausência de fonte
- **THEN** o manifesto DEVE anunciar `agregado/resumo` ou `sem-fonte`, sem inventar o caminho de um título individual

#### Scenario: Tipo ausente não é anunciado
- **WHEN** o ticker não possui um tipo de título
- **THEN** o manifesto NÃO DEVE anunciar os caminhos desse tipo

#### Scenario: Cache frio
- **WHEN** o ticker não possui cache de direitos e obrigações
- **THEN** a árvore DEVE manter o ramo navegável com a indicação de ausência de dados, sem erro e sem download

#### Scenario: Sem efeitos colaterais no chat
- **WHEN** a LLM navega os caminhos de direitos e obrigações
- **THEN** nenhum download, extração, resumo ou chamada à CVM/B3 DEVE ocorrer
