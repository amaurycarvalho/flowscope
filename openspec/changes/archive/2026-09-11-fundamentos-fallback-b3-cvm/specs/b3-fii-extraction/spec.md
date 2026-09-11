## MODIFIED Requirements

### Requirement: Listagem e extração do Informe Mensal Estruturado

O sistema DEVE listar os documentos do Informe Mensal Estruturado (`GetStructuredReports`, `type=40`) de um fundo e, para o documento ativo mais recente cuja referência não seja posterior à data de referência, baixar o HTML do FundosNet e extrair, por rótulo, o número de cotistas, o patrimônio líquido, a quantidade de cotas emitidas, o valor patrimonial por cota e a classificação autorregulação do fundo (Classificação, Subclassificação, Gestão e Segmento de Atuação). A ausência de informes DEVE resultar em ausência de dados, distinta de falha de aquisição.

#### Scenario: Informe mensal extraído
- **WHEN** o informe ativo mais recente contém os rótulos `Número de cotistas`, `Patrimônio Líquido`, `Número de Cotas Emitidas` e `Valor Patrimonial das Cotas`
- **THEN** o sistema DEVE expor o número de cotistas, o patrimônio líquido, as cotas emitidas e o VP/Cota, com a data de referência do informe

#### Scenario: Classificação autorregulação extraída
- **WHEN** o informe ativo contém o rótulo `Classificação autorregulação` com Classificação, Subclassificação, Gestão e Segmento de Atuação
- **THEN** o sistema DEVE expor esses quatro campos no informe normalizado, tolerando rótulos ausentes

#### Scenario: Sem informes no período
- **WHEN** a listagem `type=40` retorna lista vazia
- **THEN** o sistema DEVE indicar ausência de dados sem erro

#### Scenario: Falha ao baixar o documento
- **WHEN** o download do documento do FundosNet falha
- **THEN** o sistema DEVE registrar a falha como indisponibilidade, não como ausência de dados
