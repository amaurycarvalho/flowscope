## ADDED Requirements

### Requirement: Prioridade de fonte para cotistas e patrimônio

O sistema DEVE resolver o número de cotistas e o patrimônio líquido de um FII priorizando a fonte cuja informação é mais atual — a B3 (Informe Mensal Estruturado), disponível por ticker assim que o informe é entregue — e usando a CVM como fallback quando a B3 não fornecer o dado, preservando a origem e a data de referência do valor utilizado.

#### Scenario: B3 fornece o dado
- **WHEN** a B3 possui o Informe Mensal Estruturado do ticker até a data de referência
- **THEN** o sistema DEVE usar o número de cotistas e o patrimônio da B3, registrando a origem B3

#### Scenario: B3 indisponível
- **WHEN** a B3 não possui o informe do ticker e a CVM possui o registro
- **THEN** o sistema DEVE usar o número de cotistas e o patrimônio da CVM, registrando a origem CVM

#### Scenario: Nenhuma fonte disponível
- **WHEN** nem a B3 nem a CVM possuem o dado
- **THEN** o sistema DEVE indicar ausência de valor, sem impedir as demais colunas
