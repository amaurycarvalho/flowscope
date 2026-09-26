## MODIFIED Requirements

### Requirement: Cache persistente do texto extraído por documento

O sistema DEVE persistir, por documento, o texto original extraído. Para os escopos de Documentos (por ticker), o cache DEVE permanecer em `~/.cache/flowscope/document-texts/<TICKER>.json`, um arquivo por ticker indexado pela chave estável do documento (o caminho relativo à raiz de cache). Para as notícias, o cache DEVE ser particionado por ano e mês, em `~/.cache/flowscope/document-texts/NOTICIAS-<ANO>-<MES>.json`, cada arquivo indexado pela chave estável das notícias daquele ano e mês, com o particionamento derivado da própria chave estável. Em ambos os casos, a gravação DEVE ser atômica, preservando o texto dos demais documentos do mesmo arquivo, e a leitura DEVE tolerar arquivo ausente ou corrompido. O conteúdo DEVE ser exclusivamente o texto original do documento (ou o marcador de ausência de texto), sem resumo, análise ou metadados de processamento. O texto em cache NÃO DEVE ser invalidado quando o arquivo for substituído no mesmo caminho.

#### Scenario: Documento nunca convertido
- **WHEN** um documento nunca teve o texto convertido
- **THEN** a leitura DEVE resultar em ausência de texto em cache, sem erro

#### Scenario: Texto recuperado entre execuções
- **WHEN** o texto de um documento é gravado no cache e lido novamente
- **THEN** o texto DEVE ser recuperado do arquivo correspondente

#### Scenario: Cache corrompido
- **WHEN** o arquivo de cache de um documento contém JSON inválido
- **THEN** a leitura DEVE ser tolerada como ausência de texto, sem erro

#### Scenario: Gravação preserva os demais documentos
- **WHEN** o texto de um documento é gravado no cache
- **THEN** os textos dos demais documentos do mesmo arquivo DEVEM permanecer

#### Scenario: Arquivo substituído no mesmo caminho
- **WHEN** o arquivo do documento é substituído no mesmo caminho
- **THEN** o texto em cache DEVE ser reutilizado, sem invalidação

#### Scenario: Notícias particionadas por ano e mês
- **WHEN** o texto de uma notícia é gravado no cache
- **THEN** apenas o arquivo `NOTICIAS-<ANO>-<MES>.json` do ano e mês daquela notícia DEVE ser reescrito

#### Scenario: Custo de notícia limitado ao shard
- **WHEN** uma notícia é gravada ou lida em um escopo com muitos itens
- **THEN** a operação DEVE tocar apenas o shard do ano e mês daquela notícia

## ADDED Requirements

### Requirement: Migração do cache de texto de notícias para os shards

Quando existir o cache de texto de notícias no formato anterior (`document-texts/NOTICIAS.json`, um único arquivo para todas as notícias), o sistema DEVE migrar os textos para os arquivos particionados por ano e mês, sem reconverter os arquivos e derivando ano e mês da própria chave. A migração DEVE tolerar ausência ou corrupção e NÃO DEVE afetar o cache de texto dos escopos de Documentos.

#### Scenario: Migração reutiliza os textos existentes
- **WHEN** há cache de notícias no formato anterior
- **THEN** os textos DEVEM ficar disponíveis nos shards `NOTICIAS-<ANO>-<MES>.json`, sem reconversão

#### Scenario: Sem formato anterior
- **WHEN** não há cache de notícias no formato anterior
- **THEN** nenhuma migração DEVE ocorrer, sem erro

#### Scenario: Formato anterior corrompido
- **WHEN** o cache de notícias no formato anterior está corrompido
- **THEN** a migração DEVE ser tolerada como ausência de texto, sem erro

#### Scenario: Cache de Documentos não é afetado
- **WHEN** a migração do cache de notícias é executada
- **THEN** os arquivos `<TICKER>.json` dos escopos de Documentos NÃO DEVEM ser alterados
