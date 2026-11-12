## MODIFIED Requirements

### Requirement: Resolução da identidade fiscal por prioridade de fontes

O sistema DEVE resolver, por ticker, a identidade fiscal — CNPJ, razão social, administrador (nome e CNPJ) e gestor (nome e CNPJ) — consultando as fontes por prioridade, registrando a origem de cada valor e omitindo os itens que nenhuma fonte fornecer. Para FIIs, o CNPJ, o administrador e o gestor DEVEM vir da B3 (Informe Mensal) com a CVM como fallback; quando a B3 não fornecer o CNPJ ou o gestor, DEVEM ser usados, respectivamente, o CNPJ da identidade persistida por ticker e o Informe Anual da CVM. Para Papel, o sistema DEVE resolver o CNPJ e a razão social a partir da identidade da companhia na CVM, omitindo a razão social quando indisponível.

#### Scenario: Identidade fiscal de FII
- **WHEN** a B3 fornece o CNPJ, o administrador e o gestor do FII
- **THEN** o sistema DEVE expor CNPJ, administrador e gestor, registrando a origem B3 de cada valor

#### Scenario: Gestor ausente na B3
- **WHEN** a B3 fornece CNPJ e administrador, mas não o gestor, e a CVM possui o gestor no Informe Anual
- **THEN** o sistema DEVE expor o gestor da CVM, registrando a origem CVM, sem impedir os demais itens

#### Scenario: CNPJ ausente no informe da B3
- **WHEN** o Informe Mensal não fornece o CNPJ e existe identidade persistida com CNPJ para o ticker
- **THEN** o sistema DEVE expor o CNPJ da identidade persistida como origem B3, sem impedir os demais itens

#### Scenario: Identidade fiscal de FIAGRO
- **WHEN** o ativo é um FIAGRO cujo Informe Mensal da B3 contém CNPJ, administrador e gestor
- **THEN** o sistema DEVE expor os três itens mesmo que o fundo não conste no Informe Anual de FIIs da CVM

#### Scenario: Identidade fiscal de Papel
- **WHEN** o ativo é do tipo Papel e a CVM resolve o CNPJ e a razão social da companhia
- **THEN** o sistema DEVE expor CNPJ e razão social, sem administrador ou gestor

#### Scenario: Razão social ausente em Papel
- **WHEN** a CVM resolve o CNPJ do Papel, mas não fornece a razão social
- **THEN** o sistema DEVE expor apenas o CNPJ, sem impedir os demais itens

#### Scenario: Item indisponível
- **WHEN** nenhuma fonte fornece um dos itens de identidade fiscal
- **THEN** o item DEVE ser omitido, sem impedir os demais

#### Scenario: Falha de uma fonte
- **WHEN** uma fonte de identidade fiscal está indisponível para o ticker
- **THEN** o sistema DEVE usar a fonte seguinte e manter os demais tickers inalterados
