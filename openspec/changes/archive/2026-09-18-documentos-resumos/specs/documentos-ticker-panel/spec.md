## MODIFIED Requirements

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, uma linha contendo `---`, outra linha em branco e o texto integral do documento.

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

## ADDED Requirements

### Requirement: Lista Markdown do agrupamento

Ao selecionar um nó de agrupamento da árvore (ticker, ano, mês ou categoria), o sistema DEVE exibir no campo de texto uma lista textual, em Markdown, de todos os documentos contidos nesse agrupamento. O agrupamento selecionado DEVE ser o cabeçalho de nível `#` e cada sub-agrupamento contido DEVE incrementar o nível (`##`, `###`, ...). Cada documento DEVE aparecer como um item de lista seguido do seu `short_summary`.

#### Scenario: Agrupamento do ticker selecionado
- **WHEN** o usuário seleciona o nó do ticker
- **THEN** o campo de texto DEVE exibir o ticker como `#`, os anos como `##`, os meses como `###`, as categorias como `####` e os documentos como itens de lista com seus resumos curtos

#### Scenario: Agrupamento de categoria selecionado
- **WHEN** o usuário seleciona um nó de categoria
- **THEN** a categoria DEVE ser o cabeçalho de nível `#` e os documentos contidos DEVEM aparecer como itens de lista com seus resumos curtos

#### Scenario: Documento sem resumo curto na lista
- **WHEN** um documento da lista não tem `short_summary` preenchido
- **THEN** o item DEVE exibir a mensagem de resumo indisponível definida pela regra de indisponibilidade

### Requirement: Mensagem de indisponibilidade de resumo

Quando um resumo não estiver preenchido, o sistema DEVE exibir `Resumo indisponível.` seguido de ` Clique no documento para análise.` se a LLM estiver configurada, ou seguido de ` Configure a LLM via o botão I.A. e teste a comunicação.` caso contrário. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes.

#### Scenario: LLM configurada
- **WHEN** o resumo está ausente e a LLM está configurada
- **THEN** a mensagem DEVE ser `Resumo indisponível. Clique no documento para análise.`

#### Scenario: LLM não configurada
- **WHEN** o resumo está ausente e a LLM não está configurada
- **THEN** a mensagem DEVE ser `Resumo indisponível. Configure a LLM via o botão I.A. e teste a comunicação.`

### Requirement: Geração de resumo sob demanda

Ao selecionar um documento sem `long_summary` com a LLM configurada, o sistema DEVE enviar o texto integral do documento ao serviço de resumo, persistir o `short_summary` e o `long_summary` resultantes no catálogo do documento e exibir a pré-visualização composta. A geração DEVE ocorrer fora da thread da interface, com estado de carregamento, e resultados de seleções anteriores DEVEM ser descartados quando a seleção mudar.

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

### Requirement: Campo de texto somente-leitura com atalhos e cursor

O campo de texto DEVE permanecer somente-leitura, impedindo alterações de conteúdo, e ao mesmo tempo DEVE aceitar os atalhos de teclado de seleção e cópia (Ctrl+A, Ctrl+C, Shift+setas) e a navegação pelo teclado, exibindo o cursor de foco. A seleção com o mouse DEVE continuar funcionando. O atalho Ctrl+A DEVE ser vinculado explicitamente ao campo, independentemente do mapeamento padrão do toolkit.

#### Scenario: Selecionar tudo com Ctrl+A
- **WHEN** o campo de texto está focado e o usuário pressiona Ctrl+A
- **THEN** todo o conteúdo DEVE ser selecionado

#### Scenario: Ctrl+A independente do toolkit
- **WHEN** o atalho padrão de "selecionar tudo" do toolkit não estiver associado a Ctrl+A (ex.: X11, onde `<<SelectAll>>` é Ctrl+barra)
- **THEN** Ctrl+A DEVE ainda selecionar todo o conteúdo do campo

#### Scenario: Cópia com Ctrl+C
- **WHEN** o usuário pressiona Ctrl+C com texto selecionado
- **THEN** a seleção DEVE ser copiada para a área de transferência

#### Scenario: Cursor visível
- **WHEN** o campo de texto recebe o foco
- **THEN** o cursor de inserção DEVE ser visível

#### Scenario: Edição bloqueada
- **WHEN** o usuário pressiona uma tecla que alteraria o conteúdo (ex.: uma letra)
- **THEN** o conteúdo DEVE permanecer inalterado

### Requirement: Cópia do conteúdo da pré-visualização

Quando a sub-aba "Documentos" estiver ativa, o botão "Copiar dados CSV" DEVE copiar o conteúdo atual do campo de texto da pré-visualização para a área de transferência e DEVE estar habilitado nessa sub-aba mesmo sem dados da B3 carregados. Nas demais sub-abas, o botão DEVE preservar o comportamento de cópia de CSV.

#### Scenario: Documentos ativa copia a pré-visualização
- **WHEN** a sub-aba "Documentos" está ativa e o usuário aciona o botão "Copiar dados CSV"
- **THEN** o conteúdo atual do campo de texto DEVE ser copiado para a área de transferência

#### Scenario: Botão habilitado em Documentos sem dados
- **WHEN** o usuário entra na sub-aba "Documentos" sem dados da B3 carregados
- **THEN** o botão "Copiar dados CSV" DEVE estar habilitado

#### Scenario: Outra sub-aba mantém a cópia de CSV
- **WHEN** a sub-aba ativa não é "Documentos" e o usuário aciona o botão "Copiar dados CSV"
- **THEN** o CSV do contexto atual DEVE ser copiado

### Requirement: Persistência da configuração de I.A.

O botão "Salvar" do diálogo de configuração de I.A. DEVE gravar a última configuração de `llm.chat` e fechar o diálogo. A configuração DEVE permanecer no arquivo após o fechamento da aplicação, DEVE ser recarregada para uso do sistema no próximo início e DEVE aparecer preenchida quando o diálogo for reaberto. A gravação das preferências da interface NÃO DEVE sobrescrever o bloco `llm`.

#### Scenario: Salvar fecha o diálogo
- **WHEN** o usuário aciona "Salvar" no diálogo de I.A.
- **THEN** a configuração DEVE ser gravada e o diálogo DEVE ser fechado

#### Scenario: Reabertura mostra a última configuração
- **WHEN** o diálogo de I.A. é reaberto após um salvamento
- **THEN** os campos DEVEM exibir os últimos valores salvos

#### Scenario: Configuração sobrevive ao fechamento da aplicação
- **WHEN** a aplicação é fechada após salvar a configuração de I.A.
- **THEN** o bloco `llm.chat` DEVE permanecer no arquivo e ser recarregado no próximo início
