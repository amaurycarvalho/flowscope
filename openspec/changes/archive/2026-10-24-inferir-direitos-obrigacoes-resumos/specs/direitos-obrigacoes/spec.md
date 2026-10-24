## ADDED Requirements

### Requirement: Nós inferidos de direitos e obrigações

Quando existirem inferências válidas para o ticker, a árvore de "Direitos e obrigações" DEVE exibir os itens inferidos sob o papel e o tipo correspondentes, com rótulo explícito de que foram inferidos pela IA. A árvore do Chat AI DEVE expor os mesmos itens nos caminhos canônicos do ramo, sem chamadas de rede durante a navegação. Itens inferidos NÃO DEVEM ser apresentados como dados oficiais.

#### Scenario: Item inferido na árvore de documentos
- **WHEN** o ticker tem uma inferência de obrigação sem correspondência oficial
- **THEN** a sub-aba "Documentos" DEVE exibir o item sob Obrigações → Títulos → tipo, rotulado como inferido pela IA

#### Scenario: Item inferido na árvore do chat
- **WHEN** a LLM navega até o ramo de direitos e obrigações de um ticker com inferências
- **THEN** os caminhos canônicos DEVEM incluir os itens inferidos, com proveniência e sem baixar dados

#### Scenario: Ausência explícita só sem oficial e sem inferência
- **WHEN** não há dado oficial nem inferência para um tipo
- **THEN** o ramo DEVE manter a indicação de ausência de fonte

### Requirement: Precedência e proveniência na árvore

Em conflito entre um item oficial e um item inferido, a árvore DEVE manter apenas o item oficial. Para itens apenas inferidos, a pré-visualização DEVE informar o documento de origem, a data de referência e que o conteúdo foi inferido pela IA.

#### Scenario: Conflito resolvido pelo oficial
- **WHEN** o mesmo título aparece em fonte oficial e em inferência
- **THEN** a árvore DEVE exibir o item oficial e omitir a duplicata inferida

#### Scenario: Proveniência do item inferido
- **WHEN** o usuário seleciona um item inferido
- **THEN** a pré-visualização DEVE exibir documento de origem, data de referência e o aviso de inferência por IA
