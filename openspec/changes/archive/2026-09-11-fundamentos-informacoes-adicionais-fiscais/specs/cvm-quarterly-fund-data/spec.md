## ADDED Requirements

### Requirement: Percentuais por indexador do complemento

O sistema DEVE expor, por CNPJ, os percentuais de patrimônio por indexador reportados no arquivo `complemento` do Informe Trimestral (`Percentual_Indexador_Valor_Total_IGPM`, `INPC`, `IPCA` e `INCC`), selecionando o registro mais recente cuja competência não seja posterior à data de referência.

#### Scenario: Percentuais extraídos
- **WHEN** o registro do CNPJ contém percentuais de indexador
- **THEN** o sistema DEVE expor os percentuais disponíveis por indexador

#### Scenario: Competência mais recente
- **WHEN** existem registros de competências distintas para o CNPJ
- **THEN** o sistema DEVE usar o registro de competência mais recente até a data de referência

#### Scenario: Sem percentuais
- **WHEN** o CNPJ não possui percentuais de indexador no período
- **THEN** o sistema DEVE retornar ausência de dados, sem erro
