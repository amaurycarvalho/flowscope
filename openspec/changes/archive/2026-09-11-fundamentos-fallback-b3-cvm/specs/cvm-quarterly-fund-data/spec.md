## MODIFIED Requirements

### Requirement: Schema versionado e preservação bruta

O sistema DEVE identificar o schema do Informe Trimestral/DFIN pelo conjunto de colunas, aceitar as variações de layout conhecidas (longo `Descricao`/`Valor` e largo de resultado contábil-financeiro) e preservar os arquivos brutos com hash e versão do parser, falhando de forma explícita quando as colunas obrigatórias de nenhum layout conhecido estiverem presentes.

#### Scenario: Schema reconhecido
- **WHEN** o arquivo contém as colunas esperadas de identidade e componentes de um layout conhecido
- **THEN** o sistema DEVE processar os registros e registrar a versão do parser

#### Scenario: Colunas obrigatórias ausentes
- **WHEN** o arquivo não contém as colunas obrigatórias de nenhum layout conhecido
- **THEN** o sistema DEVE levantar erro de schema em vez de produzir resultado parcial

## ADDED Requirements

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
