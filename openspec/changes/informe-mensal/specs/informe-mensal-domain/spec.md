## ADDED Requirements

### Requirement: Entidade CarteiraAtivo
O sistema DEVE possuir uma entidade `CarteiraAtivo` com `ativo` (str), `quantidade` (int), `valor_mercado` (Decimal) e `percentual` (Decimal).

#### Scenario: CarteiraAtivo com todos os campos
- **WHEN** um ativo é instanciado com nome `"Tesouro Selic"`, quantidade `10000`, valor de mercado `Decimal("1050000.00")` e percentual `Decimal("12.50")`
- **THEN** todos os campos DEVEM ser acessíveis

### Requirement: Entidade Carteira
O sistema DEVE possuir uma entidade `Carteira` com lista de `CarteiraAtivo`, `total_ativos`, `total_passivos` e `patrimonio_liquido` (todos Decimal).

#### Scenario: Carteira com múltiplos ativos
- **WHEN** uma `Carteira` é criada com 3 ativos e totais
- **THEN** a lista DEVE conter 3 elementos e os totais DEVEM estar acessíveis

### Requirement: Entidade Resultados
O sistema DEVE possuir uma entidade `Resultados` com decomposição de receitas e despesas: `receitas_rendimentos`, `receitas_outras`, `despesas_administracao`, `despesas_auditoria`, `despesas_outras`, `resultado_liquido` (todos Decimal).

#### Scenario: Resultados com todas as rubricas
- **WHEN** `Resultados` é criado com todos os campos
- **THEN** todos os campos DEVEM estar acessíveis

### Requirement: Entidade Indicadores
O sistema DEVE possuir uma entidade `Indicadores` com `rentabilidade_mes`, `rentabilidade_ano`, `valor_cota`, `patrimonio_liquido` (Decimal) e `num_cotistas` (int).

#### Scenario: Indicadores com valores típicos
- **WHEN** `Indicadores` é criado com rentabilidade mês `Decimal("1.25")`, PL `Decimal("7200000")` e `12500` cotistas
- **THEN** todos os campos DEVEM estar acessíveis

### Requirement: Entidade OutrasInformacoes
O sistema DEVE possuir `OutrasInformacoes` com `taxa_administracao` (Decimal), `prazo` (str) e `categoria_anbima` (str).

### Requirement: Entidade InformeMensal
O sistema DEVE possuir `InformeMensal` agregando `ticker`, `id_fnet`, `id_documento`, `url_documento`, `data_extracao`, `periodo_referencia`, `data_entrega`, `entidade` (Entidade), `carteira`, `resultados`, `indicadores`, `outras_informacoes`, com `to_dict()` e `to_text()`.

#### Scenario: InformeMensal.to_text()
- **WHEN** `to_text()` é chamado
- **THEN** o texto DEVE conter nome, CNPJ, composição da carteira com totais, resultados, indicadores e outras informações em formato legível

### Requirement: Value Object Percentual
O sistema DEVE possuir `Percentual` que aceita strings com `%` e vírgula decimal, convertendo para `Decimal`.

#### Scenario: Percentual com símbolo e vírgula
- **WHEN** `Percentual` é instanciado com `"12,50%"`
- **THEN** o valor interno DEVE ser `Decimal("12.50")`
