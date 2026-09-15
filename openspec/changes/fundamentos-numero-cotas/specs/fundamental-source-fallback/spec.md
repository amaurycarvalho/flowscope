## ADDED Requirements

### Requirement: Prioridade de fonte para a quantidade de cotas emitidas

O sistema DEVE resolver a quantidade de cotas/ações emitidas por ticker com prioridade dependente do tipo de ativo. Para ativos do tipo `FII`, DEVE priorizar a B3 (Informe Mensal Estruturado) e usar a CVM como fallback, e o Fundamentus como fallback final. Para ativos do tipo `Papel`, DEVE usar o Fundamentus. O valor resolvido DEVE ser exposto na análise fundamentalista como a quantidade de cotas/ações emitidas, exibindo `N/A` quando nenhuma fonte fornecer o dado, sem impedir as demais colunas.

#### Scenario: FII com dado da B3
- **WHEN** a B3 possui o Informe Mensal Estruturado do FII com a quantidade de cotas emitidas
- **THEN** o sistema DEVE usar a quantidade de cotas da B3, registrando a origem B3

#### Scenario: FII com dado apenas da CVM
- **WHEN** a B3 não fornece a quantidade de cotas do FII e a CVM possui o registro
- **THEN** o sistema DEVE usar a quantidade de cotas da CVM, registrando a origem CVM

#### Scenario: FII com dado apenas do Fundamentus
- **WHEN** nem a B3 nem a CVM fornecem a quantidade de cotas do FII e o Fundamentus expõe `Nro. Cotas`
- **THEN** o sistema DEVE usar a quantidade de cotas do Fundamentus como fallback

#### Scenario: Papel usa o Fundamentus
- **WHEN** o ativo é do tipo `Papel` e o Fundamentus expõe `Nro. Ações`
- **THEN** o sistema DEVE usar a quantidade de ações do Fundamentus

#### Scenario: Nenhuma fonte disponível
- **WHEN** nenhuma fonte fornece a quantidade de cotas/ações emitidas
- **THEN** a coluna correspondente DEVE ser exibida como `N/A`, sem impedir as demais
