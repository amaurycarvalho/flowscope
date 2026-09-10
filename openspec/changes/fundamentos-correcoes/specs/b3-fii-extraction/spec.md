## MODIFIED Requirements

### Requirement: Download e extração de documento FundosNet

O sistema DEVE, para cada documento listado, obter o identificador a partir de `urlViewerFundosNet`, baixar o documento e extrair os campos estruturados do provento (entidade e provento), reutilizando as estratégias de parsing tolerantes a HTML malformado. No layout real do documento, em que `Rendimento` e `Amortização` são colunas e cada linha de atributo traz o valor na coluna aplicável, o sistema DEVE identificar o tipo do provento pela coluna que contém o valor (não pela presença de um marcador `X`) e DEVE extrair a `Data-base` mesmo quando o rótulo vier acompanhado de texto parentético (ex.: `Data-base (último dia de negociação "com" direito ao provento)`).

#### Scenario: Documento com identificador na URL
- **WHEN** a URL do documento contém `?id=<N>`
- **THEN** o sistema DEVE usar `<N>` como identificador e retornar o provento extraído

#### Scenario: Documento sem provento extraível
- **WHEN** o documento não contém um código ISIN reconhecível
- **THEN** o sistema DEVE registrar a falha daquele documento sem interromper os demais

#### Scenario: Rendimento no layout de duas colunas
- **WHEN** o documento traz as colunas `Rendimento` e `Amortização` e a linha `Data-base`/`Valor do provento` tem o valor na coluna `Rendimento`
- **THEN** o provento extraído DEVE ter tipo `Rendimento`, com `data_base` preenchida pela data da linha `Data-base`

#### Scenario: Amortização no layout de duas colunas
- **WHEN** o documento traz as colunas `Rendimento` e `Amortização` e o valor está na coluna `Amortização`
- **THEN** o provento extraído DEVE ter tipo `Amortização`

#### Scenario: Data-base com rótulo parentético
- **WHEN** o rótulo da data-base contém texto adicional entre parênteses
- **THEN** a data-base DEVE ser extraída do valor associado ao rótulo

## ADDED Requirements

### Requirement: Teste de contrato do documento FundosNet real

O sistema DEVE manter uma fixture estática de um documento FundosNet real de rendimentos e amortizações e um teste de contrato que garanta a extração de `tipo` e `data_base`, de modo que uma mudança de layout da B3 seja detectada explicitamente.

#### Scenario: Fixture real valida a extração
- **WHEN** o parser é executado sobre a fixture do documento real
- **THEN** o provento DEVE ser classificado como `Rendimento` e conter `data_base` não nula

#### Scenario: Mudança de layout detectada
- **WHEN** a fixture perde a coluna de valor ou o rótulo de data-base
- **THEN** o teste de contrato DEVE falhar explicitamente
