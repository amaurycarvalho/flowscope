## ADDED Requirements

### Requirement: Formatação numérica das colunas da tabela fundamentalista
A tabela fundamentalista DEVE formatar as colunas "Último dividendo", "Dividendo anterior", "Dividend Payout (DY/FFOY)", "P (Cotação)" e "VP (VP/Cota)" com exatamente duas casas decimais, usando vírgula como separador decimal. A coluna "Dividend Payout (DY/FFOY)" DEVE incluir o sufixo `%`; as demais DEVEM manter seus formatos (valor monetário curto e valor por cota). Quando não houver valor, a coluna DEVE exibir `N/A`.

#### Scenario: Valores com 2 casas decimais
- **WHEN** um ticker possui último dividendo `0,7`, dividendo anterior `0,5`, cotação `15,5` e VP/Cota `10`
- **THEN** a tabela DEVE exibir `0,70`, `0,50`, `15,50` e `10,00` nas respectivas colunas

#### Scenario: Dividend Payout com 2 casas decimais
- **WHEN** Dividend Yield e FFO Yield estão disponíveis e a razão entre eles é `0,894`
- **THEN** a coluna "Dividend Payout (DY/FFOY)" DEVE exibir `89,40%`

#### Scenario: Sem valor
- **WHEN** o valor de uma dessas colunas é ausente para o ticker
- **THEN** a coluna DEVE exibir `N/A`

#### Scenario: Exportação CSV consistente com a tabela
- **WHEN** o usuário copia a tabela de Fundamentos como CSV
- **THEN** os valores DEVEM usar a mesma formatação de duas casas decimais exibida na tabela
