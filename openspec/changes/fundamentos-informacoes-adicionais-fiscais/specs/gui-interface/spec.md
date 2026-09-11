## ADDED Requirements

### Requirement: Colunas Preço Típico, P / PT, Informações adicionais e Dados fiscais

A tabela fundamentalista DEVE exibir as colunas `Preço Típico` e `P / PT` logo após `P (Cotação)`, alinhadas à direita. `Preço Típico` DEVE exibir `(Max 52 sem + Min 52 sem + Cotação) / 3` e `P / PT` DEVE exibir `(Cotação − Preço Típico) / Preço Típico` como percentual; ambos DEVEM exibir `N/A` quando faltar qualquer insumo.

A tabela DEVE exibir, ao final, as colunas `Informações adicionais` e `Dados fiscais`, cujos itens são concatenados separados por ` | ` e precedidos de labels curtos. Itens sem valor em nenhuma fonte DEVEM ser omitidos; quando a coluna não tiver nenhum item, DEVE exibir `N/A`.

Para ativos do tipo Papel, `Informações adicionais` DEVE conter `LPA`, `ROE` e `ROIC`. Para FIIs, DEVE conter `Qtd Imóveis`, `Cap Rate`, `Vacância Média` e os percentuais por indexador; quando `Qtd imóveis` for zero ou desconhecido, `Qtd Imóveis`, `Cap Rate` e `Vacância Média` DEVEM ser omitidos.

Em `Dados fiscais`, FIIs DEVEM exibir `CNPJ`, `Administrador <nome> (<CNPJ>)` e `Gestor <nome> (<CNPJ>)`; Papel DEVE exibir apenas `CNPJ`. CNPJs DEVEM ser exibidos no formato `99.999.999/9999-99`.

#### Scenario: Preço Típico e P / PT calculados
- **WHEN** o ativo possui cotação, mínima e máxima de 52 semanas
- **THEN** as colunas `Preço Típico` e `P / PT` DEVEM exibir o preço típico e o desvio percentual da cotação, alinhados à direita

#### Scenario: Insumo ausente para o Preço Típico
- **WHEN** falta a cotação, a mínima ou a máxima de 52 semanas
- **THEN** as colunas `Preço Típico` e `P / PT` DEVEM exibir `N/A`

#### Scenario: Informações adicionais de Papel
- **WHEN** um ativo do tipo Papel possui LPA, ROE e ROIC
- **THEN** a coluna DEVE exibir `LPA`, `ROE` e `ROIC`, separados por ` | `

#### Scenario: Informações adicionais de FII de tijolo
- **WHEN** um FII possui `Qtd imóveis` maior que zero e demais dados disponíveis
- **THEN** a coluna DEVE exibir `Qtd Imóveis`, `Cap Rate`, `Vacância Média` e os percentuais por indexador

#### Scenario: FII sem imóveis
- **WHEN** um FII possui `Qtd imóveis` igual a zero ou desconhecido
- **THEN** a coluna NÃO DEVE exibir `Qtd Imóveis`, `Cap Rate` nem `Vacância Média`, mantendo os demais itens disponíveis

#### Scenario: Dados fiscais de FII
- **WHEN** o FII possui CNPJ, administrador e gestor com seus nomes e CNPJs
- **THEN** a coluna DEVE exibir `CNPJ`, `Administrador <nome> (<CNPJ>)` e `Gestor <nome> (<CNPJ>)`, separados por ` | `

#### Scenario: Dados fiscais de Papel
- **WHEN** o ativo é do tipo Papel e a CVM resolve o CNPJ
- **THEN** a coluna DEVE exibir apenas o `CNPJ`

#### Scenario: Item indisponível
- **WHEN** um item não está disponível em nenhuma fonte
- **THEN** ele NÃO DEVE aparecer na concatenação, sem impedir os demais

#### Scenario: Coluna sem itens
- **WHEN** nenhum item de uma das colunas está disponível para o ticker
- **THEN** a coluna DEVE exibir `N/A`

#### Scenario: Exportação CSV consistente
- **WHEN** o usuário copia a tabela de Fundamentos como CSV
- **THEN** as colunas novas DEVEM conter os mesmos textos exibidos na tabela
