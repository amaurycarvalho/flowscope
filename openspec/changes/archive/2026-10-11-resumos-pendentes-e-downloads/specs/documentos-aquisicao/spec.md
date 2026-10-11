## MODIFIED Requirements

### Requirement: Reuso de cache e tolerância a falhas

O sistema DEVE reutilizar arquivos já existentes em cache sem novo download e NÃO DEVE baixar novamente uma URL já registrada como baixada com sucesso no escopo do ticker (`deduplicacao-url`), ainda que a data de referência, o slug de categoria ou o caminho derivado tenham mudado desde o download original. Uma falha de rede ou de um documento individual DEVE ser sinalizada sem criar arquivo e sem interromper a aquisição dos demais documentos nem de outros tickers.

#### Scenario: Documento já em cache
- **WHEN** o arquivo de um documento já existe no cache
- **THEN** o sistema DEVE reutilizá-lo sem realizar novo download

#### Scenario: URL já baixada não é baixada novamente
- **WHEN** a URL de um documento já consta do registro de URLs do ticker
- **THEN** o sistema NÃO DEVE realizar nova requisição HTTP, reutilizando o arquivo canônico

#### Scenario: Caminho derivado diferente não força novo download
- **WHEN** a mesma URL reaparece com uma data ou slug de categoria que geraria outro caminho
- **THEN** o sistema NÃO DEVE baixar nem gravar novamente o documento

#### Scenario: Falha de rede isolada
- **WHEN** o download de um documento falha
- **THEN** o sistema DEVE sinalizar a falha para aquele documento, sem criar arquivo e sem interromper os demais

## ADDED Requirements

### Requirement: Data de referência com componente de hora

A data de referência de um material fact DEVE ser interpretada aceitando formatos com componente de hora (`DD/MM/AAAA HH:MM[:SS]`), descartando a hora; apenas a data DEVE ser usada para derivar ano e mês do caminho de cache. Quando o valor não for interpretável, o sistema DEVE usar a data de referência da aquisição como fallback. A mesma data de referência DEVE produzir sempre o mesmo caminho `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`.

#### Scenario: Data com hora é interpretada
- **WHEN** um material fact traz `dateReference` no formato `DD/MM/AAAA HH:MM`
- **THEN** o sistema DEVE usar apenas a data (dia, mês e ano), descartando a hora

#### Scenario: Caminho estável entre execuções
- **WHEN** o mesmo documento é adquirido novamente em uma execução posterior, com a aquisição em outro mês
- **THEN** o caminho derivado a partir da data de referência DO documento DEVE ser o mesmo e o documento NÃO DEVE ser baixado novamente

#### Scenario: Data não interpretável usa o fallback
- **WHEN** a data de referência do material fact está ausente ou em formato desconhecido
- **THEN** o sistema DEVE usar a data de referência da aquisição, sem erro
