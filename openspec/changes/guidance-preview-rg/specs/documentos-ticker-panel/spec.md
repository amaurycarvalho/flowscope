## MODIFIED Requirements

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. A extração de PDF DEVE tolerar falhas por página, preservando o texto das páginas legíveis. O texto do documento DEVE ser lido do cache persistente de texto por documento; a conversão do arquivo DEVE ocorrer apenas quando o texto ainda não estiver em cache, e o resultado DEVE ser gravado no cache para os acessos seguintes. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, pelo texto do guidance do Relatório Gerencial quando houver, por outra linha em branco, por uma linha contendo `---`, outra linha em branco e o texto integral do documento. O guidance exibido DEVE ser o do Relatório Gerencial específico selecionado e DEVE usar a mesma formatação do item da coluna `Informações adicionais` da sub-aba "Fundamentos". Para documento que não seja um Relatório Gerencial ou sem guidance avaliado, o guidance DEVE ser omitido, mantendo-se a composição pelo `long_summary`, linha em branco, `---`, linha em branco e o texto integral; na ausência de `long_summary`, o guidance, quando houver, DEVE figurar imediatamente antes do `---`.

A leitura do cache de texto e a avaliação de necessidade de resumo/guidance do documento DEVEM ocorrer fora da thread da interface; a thread do Tk DEVE apenas publicar o estado de carregamento e exibir o resultado final.

Quando o PDF estiver protegido por senha e o texto não puder ser extraído com senha vazia, o sistema DEVE solicitar a senha ao usuário em caixa de diálogo, na thread da interface, e tentar novamente a extração com a senha informada, fora da thread da interface. A solicitação DEVE ser limitada a 3 tentativas por documento/seleção (parametrizável), avisando sobre a senha incorreta e parando ao esgotar o limite. O texto obtido DEVE ser gravado no cache e a senha NÃO DEVE ser persistida. Cancelar a solicitação DEVE resultar na mensagem informativa de ausência de texto, sem erro. A solicitação DEVE ocorrer apenas no fluxo interativo de pré-visualização; o resumo em lote NÃO DEVE abrir diálogo de senha.

Quando a extração resultar parcial (ao menos uma página não extraída), a pré-visualização DEVE anotar a quantidade de páginas não extraídas antes do conteúdo. O texto parcial NÃO DEVE ser gravado no cache nem usado para gerar resumo, de modo que o documento permaneça pendente. A extração parcial DEVE ser retentada automaticamente quando o documento for selecionado ou clicado novamente e quando "Resumir pendentes" for acionado, sem controle dedicado de "Tentar novamente".

#### Scenario: Seleção de PDF
- **WHEN** o usuário seleciona um arquivo PDF
- **THEN** o sistema DEVE exibir o texto extraído do PDF na caixa somente-leitura

#### Scenario: Seleção de HTML
- **WHEN** o usuário seleciona um arquivo HTML
- **THEN** o sistema DEVE exibir o texto derivado do HTML na caixa somente-leitura

#### Scenario: Extração sem texto
- **WHEN** o arquivo não tem texto extraível
- **THEN** o sistema DEVE exibir uma mensagem informativa, sem erro

#### Scenario: Página ilegível preserva o restante
- **WHEN** um PDF tem uma página ilegível e outras legíveis
- **THEN** o sistema DEVE exibir o texto das páginas legíveis, sem erro

#### Scenario: Texto parcial é anotado
- **WHEN** um PDF é extraído parcialmente
- **THEN** a pré-visualização DEVE exibir a anotação com o número de páginas não extraídas antes do texto

#### Scenario: Texto parcial não gera resumo
- **WHEN** um PDF é extraído parcialmente e a LLM está configurada
- **THEN** o sistema NÃO DEVE gerar resumo nem persistir o texto parcial, mantendo o documento pendente

#### Scenario: Selecionar novamente retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário o seleciona ou clica nele novamente
- **THEN** o sistema DEVE refazer a extração do documento, sem exigir controle dedicado

#### Scenario: Resumir pendentes retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário aciona "Resumir pendentes"
- **THEN** o sistema DEVE refazer a extração do documento e, se completa, gerar o resumo; se ainda parcial, mantê-lo pendente

#### Scenario: PDF protegido solicita senha
- **WHEN** o usuário seleciona um PDF protegido cujo texto não foi extraído com senha vazia
- **THEN** o sistema DEVE abrir uma caixa de diálogo solicitando a senha

#### Scenario: Senha correta extrai e cacheia
- **WHEN** o usuário informa a senha correta do PDF protegido
- **THEN** o sistema DEVE extrair o texto, gravá-lo no cache e exibi-lo na pré-visualização

#### Scenario: Senha incorreta permite nova tentativa
- **WHEN** o usuário informa uma senha incorreta e ainda há tentativas disponíveis
- **THEN** o sistema DEVE informar a falha e permitir nova tentativa ou cancelamento

#### Scenario: Limite de tentativas atingido
- **WHEN** o usuário esgota as 3 tentativas de senha do documento
- **THEN** o sistema DEVE parar de solicitar a senha e exibir a mensagem informativa, sem erro

#### Scenario: Cancelamento exibe ausência de texto
- **WHEN** o usuário cancela a solicitação de senha
- **THEN** o sistema DEVE exibir a mensagem informativa de ausência de texto, sem erro

#### Scenario: Lote não solicita senha
- **WHEN** o resumo em lote processa um PDF protegido
- **THEN** o sistema NÃO DEVE abrir diálogo de senha e DEVE pular o documento

#### Scenario: Documento com resumo longo
- **WHEN** o documento selecionado tem `long_summary` preenchido
- **THEN** a caixa DEVE exibir o `long_summary`, seguido de linha em branco, `---`, linha em branco e o texto integral do documento

#### Scenario: RG com guidance intercala o texto
- **WHEN** o usuário seleciona um Relatório Gerencial com guidance avaliado
- **THEN** a caixa DEVE exibir o `long_summary`, uma linha em branco, o texto do guidance, uma linha em branco, `---`, uma linha em branco e o texto integral do documento

#### Scenario: RG sem guidance mantém a composição
- **WHEN** o usuário seleciona um Relatório Gerencial sem guidance avaliado
- **THEN** a caixa DEVE exibir a composição sem o item de guidance

#### Scenario: Documento de outra categoria não exibe guidance
- **WHEN** o usuário seleciona um documento que não é um Relatório Gerencial e existe guidance no ledger do ticker
- **THEN** a caixa NÃO DEVE exibir o item de guidance

#### Scenario: Texto lido do cache
- **WHEN** o texto de um documento já está em cache e o documento é selecionado
- **THEN** a caixa DEVE exibir o texto do cache, sem reconverter o arquivo

#### Scenario: Conversão apenas no primeiro acesso
- **WHEN** o texto de um documento não está em cache e o documento é selecionado
- **THEN** o sistema DEVE converter o arquivo, gravar o texto no cache e exibir a pré-visualização

#### Scenario: Interface não bloqueada pela leitura de cache
- **WHEN** um documento já está em cache e é selecionado
- **THEN** a thread do Tk NÃO DEVE ler o cache nem avaliar resumo/guidance antes de exibir o estado de carregamento

#### Scenario: Resultado do preview é publicado na thread do Tk
- **WHEN** o worker de pré-visualização conclui a leitura do cache e a geração do resumo
- **THEN** a pré-visualização DEVE ser aplicada à caixa somente-leitura na thread do Tk

#### Scenario: Documento já resumido abre direto
- **WHEN** o documento tem texto em cache e resumo disponível
- **THEN** a pré-visualização DEVE ser exibida sem reavaliação síncrona na thread do Tk

#### Scenario: Lote recompõe o preview com o guidance
- **WHEN** o resumo em lote é aplicado ao documento atualmente selecionado e há guidance avaliado para ele
- **THEN** a pré-visualização recomposta DEVE incluir o item de guidance
