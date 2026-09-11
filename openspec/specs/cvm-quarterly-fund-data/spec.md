# cvm-quarterly-fund-data Specification

## Purpose
Aquisição determinística do Informe Trimestral Estruturado e das Demonstrações Financeiras (DFIN) de FIIs a partir dos dados abertos da CVM, por CNPJ, normalizando os componentes de resultado que alimentam o cálculo do FFO.

## Requirements

### Requirement: Aquisição do Informe Trimestral por CNPJ

O sistema DEVE obter o Informe Trimestral Estruturado do fundo a partir dos dados abertos anuais da CVM, filtrando por CNPJ normalizado e competência, e DEVE preservar o código/identificador original de cada linha de componente, e não apenas o texto descritivo.

#### Scenario: Componentes do fundo carregados
- **WHEN** existem registros do CNPJ no Informe Trimestral da competência
- **THEN** o sistema DEVE retornar os componentes com valor, código original e descrição

#### Scenario: Código original preservado
- **WHEN** um componente é normalizado
- **THEN** o sistema DEVE manter o identificador original da linha para rastreabilidade

### Requirement: Aquisição das Demonstrações Financeiras (DFIN)

O sistema DEVE obter as DFIN anuais do fundo por CNPJ para servir de fonte de reconciliação de resultado líquido, receitas, despesas e patrimônio líquido.

#### Scenario: DFIN disponível para reconciliação
- **WHEN** o fundo possui DFIN do ano de referência
- **THEN** o sistema DEVE disponibilizar os valores para reconciliação com o resultado calculado

### Requirement: Schema versionado e preservação bruta

O sistema DEVE identificar o schema do Informe Trimestral/DFIN pelo conjunto de colunas, aceitar as variações de layout conhecidas (longo `Descricao`/`Valor` e largo de resultado contábil-financeiro) e preservar os arquivos brutos com hash e versão do parser, falhando de forma explícita quando as colunas obrigatórias de nenhum layout conhecido estiverem presentes.

#### Scenario: Schema reconhecido
- **WHEN** o arquivo contém as colunas esperadas de identidade e componentes de um layout conhecido
- **THEN** o sistema DEVE processar os registros e registrar a versão do parser

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** o arquivo não contém as colunas obrigatórias de nenhum layout conhecido
- **THEN** o sistema DEVE levantar erro de schema em vez de produzir resultado parcial

### Requirement: Tratamento de reapresentações e competência

Quando existirem múltiplos registros para o mesmo CNPJ e competência, o sistema DEVE selecionar a versão mais recente e preservar as anteriores nos dados brutos, sem assumir a posição física do registro.

#### Scenario: Múltiplas versões de um componente
- **WHEN** há mais de um registro para o mesmo CNPJ e competência
- **THEN** o sistema DEVE selecionar a versão mais recente e registrar a versão de origem

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

### Requirement: Leitura do layout largo do resultado contábil-financeiro

O sistema DEVE reconhecer o layout largo do Informe Trimestral (`inf_trimestral_fii_resultado_contabil_financeiro_*.csv`), em que cada coluna monetária representa um componente, e converter cada coluna aplicável em um componente de FFO com valor, código original e proveniência preservados. O layout longo legado (`Descricao`/`Valor`) DEVE continuar sendo aceito.

#### Scenario: Layout largo reconhecido
- **WHEN** o CSV do Informe Trimestral contém `CNPJ_Fundo_Classe`, `Data_Referencia` e colunas de resultado como `Receita_Aluguel_Investimento_Contabil`
- **THEN** o sistema DEVE processar os registros do CNPJ sem levantar erro de schema

#### Scenario: Colunas convertidas em componentes
- **WHEN** uma linha do layout largo é lida para o CNPJ
- **THEN** cada coluna monetária aplicável DEVE virar um componente com valor, código original e descrição legível

#### Scenario: Layout longo legado
- **WHEN** o CSV contém as colunas `Descricao` e `Valor`
- **THEN** o sistema DEVE continuar lendo os componentes como antes
