# deduplicacao-url Specification

## Purpose
Evitar que a mesma URL de download seja baixada mais de uma vez quando já foi concluída com sucesso, independentemente de a data, o slug de categoria ou o caminho derivado mudarem entre execuções.

## Requirements

### Requirement: Registro de URLs baixadas com sucesso por escopo

O sistema DEVE manter, por escopo, um registro das URLs cujo download foi concluído com sucesso, consultado antes de qualquer nova tentativa de download. Para documentos, o escopo DEVE ser por ticker e DEVE cobrir as raízes de cache de documentos. Para notícias, o escopo DEVE ser único e global. O registro DEVE ser gravado de forma atômica e a leitura DEVE tolerar ausência e corrupção, resultando em registro vazio.

#### Scenario: URL registrada após download bem-sucedido
- **WHEN** o download de um documento ou notícia por uma URL é concluído com sucesso e o arquivo é persistido
- **THEN** a URL DEVE ser registrada no escopo correspondente (ticker do documento ou escopo global das notícias)

#### Scenario: Registro ausente ou corrompido
- **WHEN** o arquivo do registro não existe ou contém JSON inválido
- **THEN** a leitura DEVE resultar em registro vazio, sem erro

#### Scenario: Escopos independentes
- **WHEN** a mesma URL é usada em tickers diferentes
- **THEN** o registro de um ticker NÃO DEVE impedir o download no outro

### Requirement: Consulta ao registro antes do download

Antes de baixar um documento ou notícia, o sistema DEVE verificar se a URL já consta do registro do escopo; em caso positivo, NÃO DEVE realizar nova requisição e DEVE reutilizar o resultado já persistido. A URL DEVE ser normalizada de forma determinista para servir de chave do registro.

#### Scenario: URL já baixada não é baixada novamente
- **WHEN** um documento ou notícia é processado e a sua URL já está registrada no escopo
- **THEN** o sistema NÃO DEVE realizar nova requisição HTTP para essa URL

#### Scenario: Reuso mesmo com caminho derivado diferente
- **WHEN** a mesma URL é reapresentada com uma data, slug de categoria ou caminho de destino diferente do originalmente usado
- **THEN** o sistema NÃO DEVE baixar novamente a URL

#### Scenario: URL inédita é baixada
- **WHEN** a URL não consta do registro do escopo
- **THEN** o sistema DEVE baixar o conteúdo normalmente e registrar a URL ao concluir com sucesso

### Requirement: Registro independente do hash de conteúdo

O registro de URLs DEVE ser independente do registro de hashes de conteúdo: uma URL registrada como baixada não DEVE ser descartada por o conteúdo coincidir com outro já registrado, e um conteúdo idêntico servido em URL distinta continua sujeito à deduplicação por conteúdo.

#### Scenario: Duplicata de conteúdo em URL nova ainda é deduplicada
- **WHEN** um conteúdo idêntico a outro já registrado chega por uma URL ainda não registrada
- **THEN** o sistema DEVE baixar a URL uma vez, registrar a URL e aplicar a deduplicação por conteúdo ao arquivo

#### Scenario: URL registrada não gera novo download ainda que o destino difira
- **WHEN** uma URL já registrada seria gravada em um caminho diferente por mudança de data ou categoria
- **THEN** o sistema NÃO DEVE baixar nem gravar novamente, reutilizando o arquivo canônico existente

### Requirement: Poda consistente com o cache

Quando um arquivo é removido do cache — por deduplicação ou housekeeping —, o sistema DEVE atualizar o registro de URLs para não manter uma URL como "baixada" sem arquivo correspondente disponível, de modo que uma reapresentação futura possa baixá-la novamente.

#### Scenario: Arquivo removido libera a URL
- **WHEN** o arquivo associado a uma URL registrada é removido do cache
- **THEN** a URL correspondente DEVE deixar de bloquear um novo download

#### Scenario: Demais URLs preservadas
- **WHEN** a URL de um item removido é liberada
- **THEN** o registro das demais URLs do mesmo escopo DEVE permanecer inalterado
