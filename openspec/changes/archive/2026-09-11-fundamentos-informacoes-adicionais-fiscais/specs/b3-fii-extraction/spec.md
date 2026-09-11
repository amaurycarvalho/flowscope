## ADDED Requirements

### Requirement: Extração da identidade fiscal do Informe Mensal Estruturado

O sistema DEVE extrair, por rótulo, o CNPJ do fundo e o administrador (nome e CNPJ) do HTML do Informe Mensal Estruturado do FundosNet, tolerando rótulos ausentes sem invalidar os demais campos do informe.

#### Scenario: CNPJ do fundo extraído
- **WHEN** o informe ativo contém o rótulo `CNPJ do Fundo/Classe`
- **THEN** o sistema DEVE expor o CNPJ do fundo normalizado

#### Scenario: Administrador e CNPJ extraídos
- **WHEN** o informe ativo contém os rótulos `Nome do Administrador` e `CNPJ do Administrador`
- **THEN** o sistema DEVE expor o nome e o CNPJ do administrador

#### Scenario: Rótulo ausente
- **WHEN** um dos rótulos de identidade fiscal está ausente
- **THEN** o campo correspondente DEVE ser ausência de valor, sem impedir a extração dos demais
