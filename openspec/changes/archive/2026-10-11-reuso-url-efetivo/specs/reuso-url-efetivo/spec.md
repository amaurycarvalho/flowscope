## Purpose

Garantir que uma URL já baixada com sucesso não seja baixada de novo, mesmo quando o conteúdo é descartado por duplicidade exata e o caminho derivado (data, categoria ou slug) tenha mudado, reutilizando o arquivo canônico existente.

## ADDED Requirements

### Requirement: Registro da URL no descarte por duplicidade

Quando o download de um documento ou notícia por uma URL é concluído com sucesso, mas o conteúdo é descartado por ser duplicata exata de um conteúdo já registrado, o sistema DEVE registrar a URL no escopo correspondente (ticker do documento ou escopo global das notícias), apontando para o caminho relativo canônico do arquivo já existente. A URL NÃO DEVE ser esquecida apenas porque o arquivo novo não foi gravado.

#### Scenario: Documento duplicado tem a URL registrada
- **WHEN** o download de um documento por uma URL termina em conteúdo idêntico a um já registrado no ticker
- **THEN** a URL DEVE ser registrada apontando para o arquivo canônico existente

#### Scenario: Notícia duplicada tem a URL registrada
- **WHEN** o download de uma notícia por uma URL termina em conteúdo idêntico a um já registrado no escopo global
- **THEN** a URL DEVE ser registrada apontando para o arquivo canônico existente

#### Scenario: Segunda execução não baixa de novo
- **WHEN** uma URL foi registrada no descarte por duplicidade e a mesma URL é reapresentada numa execução posterior
- **THEN** o sistema NÃO DEVE baixar a URL novamente

### Requirement: Reuso do arquivo canônico pela URL registrada

Quando a URL de um documento ou notícia já consta do registro do escopo, o sistema DEVE reutilizar o arquivo canônico associado sem nova requisição, ainda que o caminho derivado pela data, categoria ou slug gere outro destino. Se o arquivo canônico não existir mais, a URL NÃO DEVE bloquear um novo download.

#### Scenario: Caminho derivado diferente reutiliza o canônico
- **WHEN** a mesma URL reaparece com uma data de referência que geraria outro caminho e o arquivo canônico registrado ainda existe
- **THEN** o sistema NÃO DEVE baixar nem gravar novamente, reutilizando o arquivo canônico

#### Scenario: Canônico ausente libera novo download
- **WHEN** a URL está registrada, mas o arquivo canônico não existe mais no disco
- **THEN** o sistema DEVE baixar normalmente e registrar a URL para o arquivo resultante

### Requirement: Poda libera a URL do canônico removido

Quando o arquivo canônico associado a uma URL é removido do cache — por deduplicação ou housekeeping —, o sistema DEVE remover do registro as URLs que apontam para ele, de modo que uma reapresentação futura possa baixá-lo novamente. As demais URLs do mesmo escopo NÃO DEVEM ser afetadas.

#### Scenario: Arquivo canônico removido libera a URL
- **WHEN** o arquivo canônico de uma URL registrada é removido do cache
- **THEN** a URL DEVE deixar de bloquear um novo download

#### Scenario: Demais URLs preservadas
- **WHEN** a URL de um item removido é liberada
- **THEN** o registro das demais URLs do mesmo escopo DEVE permanecer inalterado
