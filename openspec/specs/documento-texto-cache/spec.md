# documento-texto-cache Specification

## Purpose

Persistir, por documento, o texto original extraído de PDF/HTML — ou o marcador de ausência de texto — de modo que a sub-aba "Documentos" e as demais funcionalidades que consomem o texto não reconvertam o arquivo a cada acesso.

## Requirements

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

### Requirement: Marcador de ausência de texto

Quando a conversão de um documento concluir que não há texto extraível (ausência
definitiva), o sistema DEVE registrar no cache o marcador `Sem texto extraível
para pré-visualização.` no lugar do texto. Quando a conversão produzir apenas
texto parcial, falhar por erro de leitura ou o documento estiver protegido por
senha, o sistema NÃO DEVE registrar o marcador nem o texto, de modo que o
documento permaneça pendente de conversão e seja tentado novamente. O marcador
DEVE ser tratado como ausência de texto por todos os consumidores do cache,
distinguindo-se de um documento ainda não convertido.

#### Scenario: Documento sem texto extraível
- **WHEN** a conversão de um documento conclui que não há texto extraível
- **THEN** o cache DEVE registrar o marcador `Sem texto extraível para pré-visualização.`

#### Scenario: Texto parcial não é persistido
- **WHEN** a conversão de um documento produz texto parcial (uma ou mais páginas não extraídas)
- **THEN** o cache NÃO DEVE registrar o texto nem o marcador, e o documento DEVE permanecer pendente de conversão

#### Scenario: Falha de conversão não é persistida
- **WHEN** a conversão de um documento falha por erro de leitura
- **THEN** o cache NÃO DEVE registrar o marcador nem texto, e o documento DEVE permanecer pendente de conversão

#### Scenario: Documento protegido não é persistido
- **WHEN** a conversão de um documento é impedida por proteção de senha
- **THEN** o cache NÃO DEVE registrar o marcador nem texto, e o documento DEVE permanecer pendente de conversão

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

### Requirement: Nova tentativa de conversão após resultado não definitivo

Um documento cuja conversão terminou de forma parcial, falhou ou cujo PDF está
protegido NÃO DEVE ser tratado como já processado: uma nova conversão DEVE ser
tentada em um novo contexto de processamento (nova seleção, novo lote ou nova
execução), sem exigir limpeza manual do cache.

#### Scenario: Falha permite nova tentativa
- **WHEN** a conversão de um documento falhou e o documento é processado novamente depois
- **THEN** o sistema DEVE tentar converter o arquivo outra vez

#### Scenario: Parcial permite nova tentativa
- **WHEN** a conversão de um documento produziu texto parcial e o documento é processado novamente
- **THEN** o sistema DEVE tentar converter o arquivo outra vez, podendo obter o texto completo

#### Scenario: Protegido permite nova tentativa com senha
- **WHEN** um documento protegido é processado novamente e uma senha válida é informada
- **THEN** o sistema DEVE extrair e persistir o texto
