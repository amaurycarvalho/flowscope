## MODIFIED Requirements

### Requirement: Tratamento de erros de aquisição e layout

O sistema DEVE distinguir e sinalizar explicitamente: ticker inexistente, layout alterado (campos obrigatórios ausentes) e falha de rede, sem retornar dados parcialmente incorretos como se fossem válidos. Uma página sem dados de papel — tabela/linhas vazias ou indicação de que nenhum papel foi encontrado — DEVE ser sinalizada como ticker não encontrado. `LayoutChanged` fica reservado à página com conteúdo parseável que perde os rótulos obrigatórios (nome e cotação).

#### Scenario: Ticker inexistente
- **WHEN** a página indica que nenhum papel foi encontrado ou não traz qualquer linha/tabela com dados de papel
- **THEN** o sistema DEVE sinalizar ticker não encontrado, e não layout alterado

#### Scenario: Layout alterado
- **WHEN** a página tem conteúdo parseável e os rótulos obrigatórios de nome e cotação estão ambos ausentes
- **THEN** o sistema DEVE sinalizar layout alterado

#### Scenario: Falha de rede
- **WHEN** a requisição falha ou retorna status de erro
- **THEN** o sistema DEVE sinalizar erro de rede sem produzir um modelo inválido

## ADDED Requirements

### Requirement: Consulta ao Fundamentus pulada para BDRs

Para ativos classificados como `BDR`, o sistema NÃO DEVE consultar o Fundamentus na composição de campos fundamentalistas nem na de FFO: NÃO DEVE realizar a requisição de rede nem sinalizar indisponibilidade da fonte, deixando esses campos para as demais fontes. Ativos não classificados como BDR mantêm a consulta normal ao Fundamentus.

#### Scenario: BDR não consulta o Fundamentus nos campos
- **WHEN** um ticker classificado como BDR é composto pelo provedor de campos fundamentalistas
- **THEN** o sistema NÃO DEVE requisitar o Fundamentus nem emitir aviso de fonte indisponível para esse ticker

#### Scenario: BDR não consulta o Fundamentus no FFO
- **WHEN** um ticker classificado como BDR é composto pelo provedor de FFO
- **THEN** o sistema NÃO DEVE requisitar o Fundamentus para esse ticker

#### Scenario: Não-BDR mantém a consulta
- **WHEN** o ticker não é classificado como BDR
- **THEN** o sistema DEVE consultar o Fundamentus normalmente
