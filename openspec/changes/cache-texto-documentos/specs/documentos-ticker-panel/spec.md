## MODIFIED Requirements

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. O texto do documento DEVE ser lido do cache persistente de texto por documento; a conversão do arquivo DEVE ocorrer apenas quando o texto ainda não estiver em cache, e o resultado DEVE ser gravado no cache para os acessos seguintes. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, uma linha contendo `---`, outra linha em branco e o texto integral do documento.

#### Scenario: Seleção de PDF
- **WHEN** o usuário seleciona um arquivo PDF
- **THEN** o sistema DEVE exibir o texto extraído do PDF na caixa somente-leitura

#### Scenario: Seleção de HTML
- **WHEN** o usuário seleciona um arquivo HTML
- **THEN** o sistema DEVE exibir o texto derivado do HTML na caixa somente-leitura

#### Scenario: Extração sem texto
- **WHEN** o arquivo não tem texto extraível
- **THEN** o sistema DEVE exibir uma mensagem informativa, sem erro

#### Scenario: Documento com resumo longo
- **WHEN** o documento selecionado tem `long_summary` preenchido
- **THEN** a caixa DEVE exibir o `long_summary`, seguido de linha em branco, `---`, linha em branco e o texto integral do documento

#### Scenario: Texto lido do cache
- **WHEN** o texto de um documento já está em cache e o documento é selecionado
- **THEN** a caixa DEVE exibir o texto do cache, sem reconverter o arquivo

#### Scenario: Conversão apenas no primeiro acesso
- **WHEN** o texto de um documento não está em cache e o documento é selecionado
- **THEN** o sistema DEVE converter o arquivo, gravar o texto no cache e exibir a pré-visualização

### Requirement: Geração de resumo sob demanda

Ao selecionar um documento sem `long_summary` com a LLM configurada, o sistema DEVE enviar o texto integral do documento ao serviço de resumo, persistir o `short_summary` e o `long_summary` resultantes no catálogo do documento e exibir a pré-visualização composta. A geração DEVE ocorrer fora da thread da interface, com estado de carregamento, e resultados de seleções anteriores DEVEM ser descartados quando a seleção mudar. Quando não houver texto extraível para o documento, o sistema NÃO DEVE gerar resumo nem chamar a LLM, exibindo o marcador de ausência de texto.

#### Scenario: Documento sem resumo com LLM configurada
- **WHEN** o usuário seleciona um documento sem `long_summary` e a LLM está configurada
- **THEN** o sistema DEVE gerar os dois resumos, persistí-los e exibir o `long_summary` seguido de `---` e do texto do documento

#### Scenario: Resumo gerado fica disponível na lista
- **WHEN** o resumo de um documento é gerado
- **THEN** uma seleção posterior do agrupamento DEVE exibir o `short_summary` desse documento

#### Scenario: Resultado obsoleto descartado
- **WHEN** o usuário troca a seleção enquanto um resumo é gerado
- **THEN** o resultado da geração anterior NÃO DEVE ser exibido para a nova seleção

#### Scenario: LLM não configurada
- **WHEN** o usuário seleciona um documento sem `long_summary` e a LLM não está configurada
- **THEN** o sistema DEVE exibir a mensagem de indisponibilidade como `long_summary`, sem chamar a LLM

#### Scenario: Falha na geração
- **WHEN** a geração do resumo falha por indisponibilidade, comunicação, provedor ou cota
- **THEN** o sistema DEVE exibir a mensagem de indisponibilidade, sem interromper a interface

#### Scenario: Sem texto extraível não gera resumo
- **WHEN** o documento não tem texto extraível e a LLM está configurada
- **THEN** o sistema NÃO DEVE chamar a LLM nem persistir resumo, exibindo o marcador de ausência de texto

## ADDED Requirements

### Requirement: Rolagem vertical na árvore e na pré-visualização

A árvore de documentos e o campo de texto da pré-visualização DEVEM exibir uma barra de rolagem vertical visível e funcional, inclusive quando o painel for mais estreito que a largura requisitada pelo conteúdo. A rolagem vertical DEVE funcionar pela barra e pela roda do mouse.

#### Scenario: Barra visível na árvore
- **WHEN** a sub-aba "Documentos" exibe a árvore
- **THEN** a barra de rolagem vertical da árvore DEVE estar visível e mapeada

#### Scenario: Barra visível na pré-visualização
- **WHEN** a sub-aba "Documentos" exibe o campo de texto
- **THEN** a barra de rolagem vertical do campo DEVE estar visível e mapeada

#### Scenario: Painel estreito não oculta a barra
- **WHEN** o painel da árvore ou da pré-visualização é mais estreito que a largura requisitada pelo conteúdo
- **THEN** a barra de rolagem vertical DEVE permanecer visível

#### Scenario: Rolagem pela roda do mouse
- **WHEN** o ponteiro está sobre a árvore ou sobre o campo de texto e o usuário usa a roda do mouse
- **THEN** o conteúdo DEVE rolar verticalmente
