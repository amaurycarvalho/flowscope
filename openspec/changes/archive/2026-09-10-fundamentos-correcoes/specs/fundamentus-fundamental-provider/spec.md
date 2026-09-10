## MODIFIED Requirements

### Requirement: Exposição do campo VP/Cota

O sistema DEVE expor o valor patrimonial por cota/ação na composição de campos fundamentalistas consumida pela análise fundamentalista. Para FIIs, DEVE usar o indicador `VP/Cota`; para ações, DEVE usar o indicador `VPA` (valor patrimonial por ação) quando `VP/Cota` estiver ausente. O campo exposto DEVE ser `vp_cota` com o valor normalizado.

#### Scenario: VP/Cota disponível
- **WHEN** a página do FII contém o indicador `VP/Cota`
- **THEN** o campo `vp_cota` DEVE ser exposto com o valor normalizado

#### Scenario: VPA disponível para ação
- **WHEN** a página da ação contém o indicador `VPA` e não contém `VP/Cota`
- **THEN** o campo `vp_cota` DEVE ser exposto com o valor do `VPA`

#### Scenario: VP/Cota ausente
- **WHEN** a página não contém o indicador `VP/Cota` nem `VPA`
- **THEN** o campo DEVE ser ausente, sem impedir a exposição dos demais campos

## ADDED Requirements

### Requirement: Histórico de proventos por ticker

O sistema DEVE obter o histórico de proventos de um ticker a partir da página `proventos.php?papel={TICKER}`, normalizando cada linha em um dividendo com data-base (coluna `Data`), valor por unidade (coluna `Valor`) e origem Fundamentus. Linhas sem data ou sem valor DEVEM ser ignoradas. A ausência de proventos DEVE resultar em lista vazia, distinta de falha de aquisição.

#### Scenario: Histórico extraído para ação
- **WHEN** a página de proventos de uma ação contém linhas com `Data`, `Valor` e `Tipo`
- **THEN** o sistema DEVE retornar uma lista de dividendos com data-base e valor, preservando a origem Fundamentus

#### Scenario: Tipos de provento de ação
- **WHEN** uma linha tem `Tipo` igual a `DIVIDENDO`, `DIVIDENDO MENSAL`, `JRS CAP PROPRIO` ou `JUROS`
- **THEN** o provento DEVE ser tratado como dividendo (rendimento), nunca como amortização

#### Scenario: Sem proventos
- **WHEN** a página não contém linhas de proventos
- **THEN** o sistema DEVE retornar lista vazia sem erro

#### Scenario: Falha de rede
- **WHEN** a requisição à página de proventos falha
- **THEN** o sistema DEVE sinalizar indisponibilidade, sem retornar dados parciais como se estivessem completos
