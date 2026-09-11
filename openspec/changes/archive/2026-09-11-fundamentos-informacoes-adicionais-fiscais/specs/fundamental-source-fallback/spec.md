## ADDED Requirements

### Requirement: Resolução da identidade fiscal por prioridade de fontes

O sistema DEVE resolver, por ticker, a identidade fiscal — CNPJ, administrador (nome e CNPJ) e gestor (nome e CNPJ) — consultando as fontes por prioridade, registrando a origem de cada valor e omitindo os itens que nenhuma fonte fornecer. Para FIIs, o CNPJ e o administrador DEVEM vir da B3 (Informe Mensal) com a CVM como fallback, e o gestor do Informe Anual da CVM. Para Papel, o sistema DEVE resolver apenas o CNPJ, a partir da identidade da companhia na CVM.

#### Scenario: Identidade fiscal de FII
- **WHEN** a B3 fornece o CNPJ e o administrador do FII e a CVM fornece o gestor
- **THEN** o sistema DEVE expor CNPJ, administrador e gestor, registrando a origem de cada valor

#### Scenario: Identidade fiscal de Papel
- **WHEN** o ativo é do tipo Papel e a CVM resolve o CNPJ da companhia
- **THEN** o sistema DEVE expor apenas o CNPJ, sem administrador ou gestor

#### Scenario: Item indisponível
- **WHEN** nenhuma fonte fornece um dos itens de identidade fiscal
- **THEN** o item DEVE ser omitido, sem impedir os demais

#### Scenario: Falha de uma fonte
- **WHEN** uma fonte de identidade fiscal está indisponível para o ticker
- **THEN** o sistema DEVE usar a fonte seguinte e manter os demais tickers inalterados
