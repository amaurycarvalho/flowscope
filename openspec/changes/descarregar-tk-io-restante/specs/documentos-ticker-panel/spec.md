## MODIFIED Requirements

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. O texto do documento DEVE ser lido do cache persistente de texto por documento; a conversão do arquivo DEVE ocorrer apenas quando o texto ainda não estiver em cache, e o resultado DEVE ser gravado no cache para os acessos seguintes. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, uma linha contendo `---`, outra linha em branco e o texto integral do documento.

A leitura do cache de texto e a avaliação de necessidade de resumo/guidance do documento DEVEM ocorrer fora da thread da interface; a thread do Tk DEVE apenas publicar o estado de carregamento e exibir o resultado final.

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

#### Scenario: Interface não bloqueada pela leitura de cache
- **WHEN** um documento já está em cache e é selecionado
- **THEN** a thread do Tk NÃO DEVE ler o cache nem avaliar resumo/guidance antes de exibir o estado de carregamento

#### Scenario: Resultado do preview é publicado na thread do Tk
- **WHEN** o worker de pré-visualização conclui a leitura do cache e a geração do resumo
- **THEN** a pré-visualização DEVE ser aplicada à caixa somente-leitura na thread do Tk

#### Scenario: Documento já resumido abre direto
- **WHEN** o documento tem texto em cache e resumo disponível
- **THEN** a pré-visualização DEVE ser exibida sem reavaliação síncrona na thread do Tk
