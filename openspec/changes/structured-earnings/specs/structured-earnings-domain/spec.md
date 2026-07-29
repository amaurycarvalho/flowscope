## ADDED Requirements

### Requirement: Entidade Entidade
O sistema DEVE possuir uma entidade de domínio `Entidade` representando uma empresa ou fundo listado, contendo obrigatoriamente os campos `nome`, `cnpj` (CNPJ), `nome_administrador`, `cnpj_administrador` (CNPJ), `responsavel`, `telefone`.

#### Scenario: Criação de entidade com todos os campos
- **WHEN** uma entidade é instanciada com nome, CNPJ, administrador, responsavel e telefone
- **THEN** todos os campos DEVEM ser acessíveis como atributos da entidade

### Requirement: Entidade Provento
O sistema DEVE possuir uma entidade de domínio `Provento` representando um pagamento de rendimento ou amortização, contendo obrigatoriamente `codigo_isin` (ISIN), `codigo_negociacao`, `tipo` (Rendimento/Amortização), `data_base`, `valor_por_unidade` (ValorProvento), `data_pagamento`, `periodo_referencia`, `isento_ir`, `nota_isencao`.

#### Scenario: Provento do tipo Rendimento
- **WHEN** um provento é criado com `tipo="Rendimento"` e `valor_por_unidade=0.08355`
- **THEN** o atributo `tipo` DEVE ser "Rendimento" e `valor_por_unidade` DEVE ser um Decimal equivalente a 0.08355

#### Scenario: Provento do tipo Amortização
- **WHEN** um provento é criado com `tipo="Amortização"` e `valor_por_unidade=1.50`
- **THEN** o atributo `tipo` DEVE ser "Amortização" e `valor_por_unidade` DEVE ser um Decimal equivalente a 1.50

### Requirement: Value Object CNPJ
O sistema DEVE possuir um value object `CNPJ` que valida e armazena um CNPJ no formato `XX.XXX.XXX/XXXX-XX`, lançando `ValueError` para formatos inválidos.

#### Scenario: CNPJ válido
- **WHEN** um CNPJ é instanciado com `"28.737.771/0001-85"`
- **THEN** o value object DEVE ser criado com sucesso e seu valor DEVE ser acessível

#### Scenario: CNPJ inválido
- **WHEN** um CNPJ é instanciado com formato inválido (ex: `"123"`)
- **THEN** uma exceção `ValueError` DEVE ser lançada

### Requirement: Value Object ISIN
O sistema DEVE possuir um value object `ISIN` que valida e armazena um código ISIN no formato `BRXXXXXXXXXX` (12 caracteres), lançando `ValueError` para formatos inválidos.

#### Scenario: ISIN válido
- **WHEN** um ISIN é instanciado com `"BRALZRCTF006"`
- **THEN** o value object DEVE ser criado com sucesso e seu valor DEVE ser acessível

#### Scenario: ISIN inválido
- **WHEN** um ISIN é instanciado com menos de 12 caracteres
- **THEN** uma exceção `ValueError` DEVE ser lançada

### Requirement: Value Object ValorProvento
O sistema DEVE possuir um value object `ValorProvento` que encapsula um valor monetário (Decimal), similar a `Price`, aceitando strings com `R$`, vírgula como separador decimal e ponto como separador de milhar.

#### Scenario: Valor monetário brasileiro
- **WHEN** um ValorProvento é instanciado com `"R$ 0,08355"`
- **THEN** o valor interno DEVE ser `Decimal("0.08355")`

#### Scenario: Valor puramente numérico
- **WHEN** um ValorProvento é instanciado com `Decimal("1.50")`
- **THEN** o valor interno DEVE ser `Decimal("1.50")`

### Requirement: Entidade DocumentoProvento
O sistema DEVE possuir uma entidade agregadora `DocumentoProvento` que combina os dados de uma `Entidade`, um `Provento`, metadados de contato e informação, e metadados de extração (`ticker`, `id_fnet`, `id_documento`, `url_documento`, `data_extracao`). A entidade DEVE implementar `DocumentoIndexavel` com método `to_text()`.

#### Scenario: DocumentoProvento completo
- **WHEN** um DocumentoProvento é criado com entidade, provento, contato, informacao e metadados de extração
- **THEN** todos os componentes DEVEM ser acessíveis como atributos da entidade

#### Scenario: DocumentoProvento.to_text()
- **WHEN** `to_text()` é chamado
- **THEN** o texto DEVE conter nome, CNPJ, ticker, tipo de provento, valor, data, isento IR e nota de isenção em formato legível para embedding
