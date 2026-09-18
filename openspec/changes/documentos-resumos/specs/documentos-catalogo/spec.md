## ADDED Requirements

### Requirement: Campos de resumo no catálogo

Cada documento do catálogo DEVE expor `short_summary` e `long_summary`, ambos nulos quando ainda não gerados. O catálogo DEVE preencher esses campos a partir do armazenamento de resumos do ticker ao ser consultado.

#### Scenario: Documento sem resumo
- **WHEN** o catálogo é consultado para um ticker cujos documentos não têm resumo armazenado
- **THEN** `short_summary` e `long_summary` DEVEM ser nulos para esses documentos

#### Scenario: Documento com resumo armazenado
- **WHEN** existe resumo armazenado para um documento do ticker
- **THEN** o catálogo DEVE expor o `short_summary` e o `long_summary` armazenados nesse documento

### Requirement: Persistência de resumos por ticker

O sistema DEVE persistir os resumos em `~/.cache/flowscope/document-summaries/<TICKER>.json`, um arquivo por ticker, com escrita atômica e tolerância a arquivo ausente ou corrompido. Cada resumo DEVE ser associado a uma chave estável do documento, derivada do caminho do arquivo relativo à raiz de cache (por exemplo, `bdr/ALZR11/2026/02/10.pdf`), de modo que o mesmo documento recupere seu resumo em execuções futuras.

#### Scenario: Resumo recuperado entre execuções
- **WHEN** um resumo é gravado e o catálogo é consultado novamente
- **THEN** o resumo DEVE ser recuperado do arquivo do ticker

#### Scenario: Arquivo de resumos ausente
- **WHEN** o arquivo de resumos do ticker não existe
- **THEN** a leitura DEVE retornar sem resumos, sem erro

#### Scenario: Arquivo de resumos corrompido
- **WHEN** o arquivo de resumos do ticker contém JSON inválido
- **THEN** a leitura DEVE ser tolerada sem erro, tratando o ticker como sem resumos

### Requirement: Gravação de resumo de um documento

O sistema DEVE permitir gravar o `short_summary` e o `long_summary` de um documento específico, preservando os resumos dos demais documentos do mesmo ticker.

#### Scenario: Gravar resumo sem afetar os demais
- **WHEN** o resumo de um documento é gravado
- **THEN** os resumos já existentes de outros documentos do ticker DEVEM permanecer inalterados

#### Scenario: Sobrescrever resumo existente
- **WHEN** um documento já possui resumo e um novo resumo é gravado
- **THEN** os valores anteriores DEVEM ser substituídos pelos novos
