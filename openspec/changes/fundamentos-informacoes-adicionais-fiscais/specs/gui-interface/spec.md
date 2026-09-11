## ADDED Requirements

### Requirement: Colunas Informações adicionais e Dados fiscais

A tabela fundamentalista DEVE exibir, ao final, as colunas `Informações adicionais` e `Dados fiscais`, cujos itens são concatenados separados por `, ` e precedidos de labels curtos. Itens sem valor em nenhuma fonte DEVEM ser omitidos; quando a coluna não tiver nenhum item, DEVE exibir `N/A`.

Para ativos do tipo Papel, `Informações adicionais` DEVE conter `LPA`, `ROE`, `ROIC`, `Preço Típico` e `%Preço Típico`. Para FIIs, DEVE conter `Qtd Imóveis`, `Cap Rate`, `Vacância Média`, `Preço Típico`, `%Preço Típico` e os percentuais por indexador; quando `Qtd imóveis` for zero ou desconhecido, `Qtd Imóveis`, `Cap Rate` e `Vacância Média` DEVEM ser omitidos.

Em `Dados fiscais`, FIIs DEVEM exibir `CNPJ`, `Administrador (CNPJ)` e `Gestor (CNPJ)`; Papel DEVE exibir apenas `CNPJ`.

#### Scenario: Informações adicionais de Papel
- **WHEN** um ativo do tipo Papel possui LPA, ROE, ROIC, mínima/máxima de 52 semanas e cotação
- **THEN** a coluna DEVE exibir `LPA`, `ROE`, `ROIC`, `Preço Típico` e `%Preço Típico`, separados por vírgula

#### Scenario: Informações adicionais de FII de tijolo
- **WHEN** um FII possui `Qtd imóveis` maior que zero e demais dados disponíveis
- **THEN** a coluna DEVE exibir `Qtd Imóveis`, `Cap Rate`, `Vacância Média`, `Preço Típico`, `%Preço Típico` e os percentuais por indexador

#### Scenario: FII sem imóveis
- **WHEN** um FII possui `Qtd imóveis` igual a zero ou desconhecido
- **THEN** a coluna NÃO DEVE exibir `Qtd Imóveis`, `Cap Rate` nem `Vacância Média`, mantendo os demais itens disponíveis

#### Scenario: Dados fiscais de FII
- **WHEN** o FII possui CNPJ, administrador e gestor com seus CNPJs
- **THEN** a coluna DEVE exibir `CNPJ`, `Administrador (CNPJ)` e `Gestor (CNPJ)`

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
- **THEN** as duas novas colunas DEVEM conter os mesmos textos exibidos na tabela
