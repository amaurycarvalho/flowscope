## ADDED Requirements

### Requirement: Estratégia de extração por rótulo
O sistema DEVE implementar uma estratégia de extração de dados baseada em busca por rótulos textuais no HTML (ex: `"Nome:"`, `"CNPJ:"`), capturando o valor associado ao rótulo no elemento seguinte ou no mesmo elemento após dois-pontos.

#### Scenario: Extração de rótulo com valor no próximo sibling
- **WHEN** o HTML contém `<strong>Nome:</strong>` seguido de `<span>ALIANZA TRUST...</span>`
- **THEN** a estratégia DEVE retornar `"ALIANZA TRUST..."` como valor associado

#### Scenario: Rótulo não encontrado
- **WHEN** o HTML não contém o rótulo procurado
- **THEN** a estratégia DEVE retornar `None`

### Requirement: Estratégia de extração por tabelas
O sistema DEVE implementar uma estratégia de extração que identifica e parseia tabelas HTML (`<table>`), extraindo cabeçalhos de `<thead><th>` ou da primeira linha de `<tbody><td>`, e convertendo cada linha em um dicionário chave-valor.

#### Scenario: Tabela com thead e múltiplas linhas
- **WHEN** o HTML contém tabela com `<thead><tr><th>Código ISIN</th><th>Valor</th></tr></thead>` e dados
- **THEN** a estratégia DEVE retornar lista de dicionários com cabeçalhos como chaves

#### Scenario: Tabela sem thead usando primeira linha como cabeçalho
- **WHEN** o HTML contém uma tabela sem `<thead>` onde a primeira `<tr>` contém `<td>Código</td><td>Valor</td>`
- **THEN** a estratégia DEVE usar a primeira linha como cabeçalho e parsear as linhas seguintes como dados

### Requirement: Identificação de contexto de tabela
O sistema DEVE identificar o contexto de cada tabela buscando elementos de cabeçalho (`<h2>`, `<h3>`, `<h4>`, `<strong>`, `<b>`) ou `<caption>` imediatamente anteriores à tabela.

#### Scenario: Tabela precedida por heading
- **WHEN** uma tabela é precedida por `<h3>Detalhes do Provento</h3>`
- **THEN** o contexto da tabela DEVE ser identificado como `"Detalhes do Provento"`

### Requirement: Identificação de tipo de provento
O sistema DEVE identificar se o provento é do tipo "Rendimento" ou "Amortização" verificando qual coluna está marcada com `"X"` na tabela extraída.

#### Scenario: Provento marcado como Rendimento
- **WHEN** a linha da tabela contém `"Rendimento": "X"` e `"Amortização": ""`
- **THEN** o tipo identificado DEVE ser `"Rendimento"`

### Requirement: Extração de isenção de IR
O sistema DEVE identificar se o provento é isento de imposto de renda buscando pelo rótulo `"Rendimento isento de IR*"` ou similar, convertendo `"Sim"` para `True` e `"Não"` para `False`.

#### Scenario: Provento isento de IR
- **WHEN** o HTML contém `"Rendimento isento de IR*: Sim"`
- **THEN** o campo `isentoIR` DEVE ser `True`

### Requirement: Limpeza de valor monetário
O sistema DEVE converter strings de valor monetário brasileiro para `Decimal`, removendo prefixo `"R$"`, pontos de milhar e convertendo vírgula decimal para ponto.

#### Scenario: Valor com símbolo e vírgula
- **WHEN** a string é `"R$ 1.234,56"`
- **THEN** o resultado DEVE ser `Decimal("1234.56")`

### Requirement: Conversão de data brasileira para ISO
O sistema DEVE converter strings de data no formato `DD/MM/AAAA` para o formato ISO `AAAA-MM-DD`.

#### Scenario: Data brasileira válida
- **WHEN** a string é `"18/06/2026"`
- **THEN** o resultado DEVE ser `"2026-06-18"`

### Requirement: Fallback para seletores alternativos
O sistema DEVE, quando as estratégias primárias (rótulo e tabela) não encontrarem um campo, tentar estratégias de fallback como busca por expressões regulares ou seletores CSS específicos antes de retornar `None`.
