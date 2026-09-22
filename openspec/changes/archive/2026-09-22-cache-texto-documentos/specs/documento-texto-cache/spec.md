## Purpose

Persistir, por documento, o texto original extraído de PDF/HTML — ou o marcador de ausência de texto — de modo que a sub-aba "Documentos" e as demais funcionalidades que consomem o texto não reconvertam o arquivo a cada acesso.

## ADDED Requirements

### Requirement: Cache persistente do texto extraído por documento

O sistema DEVE persistir, por documento, o texto original extraído, em `~/.cache/flowscope/document-texts/<TICKER>.json`, um arquivo por ticker indexado pela chave estável do documento (o caminho relativo à raiz de cache). A gravação DEVE ser atômica, preservando o texto dos demais documentos do ticker, e a leitura DEVE tolerar arquivo ausente ou corrompido. O conteúdo DEVE ser exclusivamente o texto original do documento (ou o marcador de ausência de texto), sem resumo, análise ou metadados de processamento. O texto em cache NÃO DEVE ser invalidado quando o arquivo for substituído no mesmo caminho.

#### Scenario: Documento nunca convertido
- **WHEN** um documento nunca teve o texto convertido
- **THEN** a leitura DEVE resultar em ausência de texto em cache, sem erro

#### Scenario: Texto recuperado entre execuções
- **WHEN** o texto de um documento é gravado no cache e lido novamente
- **THEN** o texto DEVE ser recuperado do arquivo do ticker

#### Scenario: Cache corrompido
- **WHEN** o arquivo de cache do ticker contém JSON inválido
- **THEN** a leitura DEVE ser tolerada como ausência de texto, sem erro

#### Scenario: Gravação preserva os demais documentos
- **WHEN** o texto de um documento é gravado no cache do ticker
- **THEN** os textos dos demais documentos do ticker DEVEM permanecer no arquivo

#### Scenario: Arquivo substituído no mesmo caminho
- **WHEN** o arquivo do documento é substituído no mesmo caminho
- **THEN** o texto em cache DEVE ser reutilizado, sem invalidação

### Requirement: Marcador de ausência de texto

Quando a conversão não produzir texto, o sistema DEVE registrar no cache o marcador `Sem texto extraível para pré-visualização.` no lugar do texto. O marcador DEVE ser tratado como ausência de texto por todos os consumidores do cache, distinguindo-se de um documento ainda não convertido.

#### Scenario: Documento sem texto extraível
- **WHEN** a conversão de um documento não produz texto
- **THEN** o cache DEVE registrar o marcador `Sem texto extraível para pré-visualização.`

#### Scenario: Marcador distinto de não convertido
- **WHEN** a entrada de cache de um documento contém o marcador de ausência
- **THEN** os consumidores DEVEM tratá-la como ausência de texto, e não como documento pendente de conversão

### Requirement: Leitura sem reconversão

A leitura de um documento cujo texto já está em cache DEVE reutilizar o conteúdo persistido, sem executar novamente a conversão do arquivo.

#### Scenario: Acesso subsequente reutiliza o cache
- **WHEN** o texto de um documento já está em cache e o documento é acessado novamente
- **THEN** o texto em cache DEVE ser usado e nenhuma nova conversão DEVE ser executada

#### Scenario: Primeiro acesso converte e grava
- **WHEN** não há texto em cache para o documento
- **THEN** o sistema DEVE converter o arquivo, gravar o resultado no cache e disponibilizá-lo
