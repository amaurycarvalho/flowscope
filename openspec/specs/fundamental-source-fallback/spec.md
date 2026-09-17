# fundamental-source-fallback Specification

## Purpose
Composição de fontes fundamentalistas com prioridade por campo, usando o Fundamentus como fonte primária e B3, CVM e o motor de FFO como fallback, preservando a proveniência da origem de cada valor consumido pela análise fundamentalista.

## Requirements

### Requirement: Prioridade por campo na composição de fontes

O sistema DEVE resolver cada campo da análise fundamentalista consultando as fontes em ordem de prioridade, com o Fundamentus como primário, e DEVE usar a primeira fonte que fornecer o campo.

#### Scenario: Campo presente no Fundamentus
- **WHEN** o Fundamentus fornece `P/VP` para o ticker
- **THEN** o sistema DEVE usar o valor do Fundamentus sem consultar o fallback para esse campo

#### Scenario: Campo ausente no Fundamentus
- **WHEN** o Fundamentus não fornece `P/VP` para o ticker
- **THEN** o sistema DEVE buscar `P/VP` no fallback (CVM) e usar o valor encontrado

### Requirement: Fallback por falha de conexão ou scraping

Quando a aquisição no Fundamentus falhar (rede, layout alterado ou ticker não encontrado), o sistema DEVE continuar a análise usando as fontes de fallback, sem interromper os demais tickers.

#### Scenario: Fundamentus indisponível
- **WHEN** a requisição ao Fundamentus falha para um ticker
- **THEN** o sistema DEVE compor os campos com B3/CVM/motor de FFO e manter a linha do ticker na tabela

#### Scenario: Isolamento entre tickers
- **WHEN** um ticker falha em todas as fontes
- **THEN** os demais tickers DEVEM continuar sendo processados normalmente

### Requirement: Proveniência da origem por campo

O sistema DEVE registrar, para cada campo composto, qual fonte forneceu o valor, permitindo explicar a origem dos dados exibidos.

#### Scenario: Origem registrada
- **WHEN** um campo é resolvido pelo fallback
- **THEN** o sistema DEVE registrar a fonte de fallback como origem daquele campo

#### Scenario: Origem do valor primário
- **WHEN** um campo é resolvido pelo Fundamentus
- **THEN** o sistema DEVE registrar o Fundamentus como origem daquele campo

### Requirement: Integração com a análise fundamentalista

O provider composto DEVE alimentar a análise fundamentalista como caminho primário, mantendo as métricas disponíveis e exibindo `N/A` apenas quando nenhuma fonte fornecer o dado.

#### Scenario: Métricas preenchidas pelo primário
- **WHEN** o Fundamentus fornece FFO Yield, Dividend Yield e P/VP
- **THEN** a análise fundamentalista DEVE exibir essas métricas preenchidas

#### Scenario: Métrica indisponível em todas as fontes
- **WHEN** nenhuma fonte fornece um dado (ex.: última data-com)
- **THEN** a métrica correspondente DEVE ser exibida como `N/A` sem impedir as demais

### Requirement: Configuração da ordem de prioridade

A ordem das fontes de fallback DEVE ser configurável, com o Fundamentus como primário por padrão, permitindo substituir fontes sem alterar a análise fundamentalista.

#### Scenario: Ordem padrão
- **WHEN** nenhuma configuração é informada
- **THEN** o sistema DEVE usar Fundamentus como primário e B3/CVM/motor de FFO como fallback

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

### Requirement: Fallback de cotação, VP/Cota e data de referência

Quando o Fundamentus não fornecer cotação, valor patrimonial por cota ou a data de referência de mercado, o sistema DEVE preencher esses campos a partir das fontes de fallback — preço de fechamento da B3 e patrimônio do Informe Mensal da B3/CVM — registrando a origem do valor utilizado.

#### Scenario: Cotação ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a cotação de um ticker e a B3 possui o último fechamento até a data de referência
- **THEN** o sistema DEVE usar o preço da B3 como `P (Cotação)`

#### Scenario: VP/Cota ausente no Fundamentus
- **WHEN** o Fundamentus não fornece `VP/Cota` e o patrimônio da B3 ou da CVM está disponível
- **THEN** o sistema DEVE preencher `VP (VP/Cota)` com o valor patrimonial por cota da fonte, ou derivá-lo de `patrimônio líquido / cotas`

#### Scenario: Data de referência ausente no Fundamentus
- **WHEN** o Fundamentus não fornece a data de última cotação e existe preço de fechamento da B3
- **THEN** o sistema DEVE usar a data do último fechamento da B3 como `Data de referência`

#### Scenario: Nenhuma fonte fornece o campo
- **WHEN** nem o Fundamentus nem a B3/CVM fornecem o campo
- **THEN** a coluna correspondente DEVE ser exibida como `N/A` sem impedir as demais

### Requirement: Fallback do Preço Típico pela janela de mercado em cache

Quando o Fundamentus não fornecer a máxima e a mínima de 52 semanas, o sistema DEVE preencher os extremos com o menor preço mínimo e o maior preço máximo da janela de mercado da B3 já carregada em cache para a análise, restrita a 52 semanas antes da data de referência, sem realizar novo acesso à B3, e DEVE calcular `Preço Típico` e `P / PT` a partir desses extremos. Quando a janela em cache não tiver nenhum dia válido, `Preço Típico` e `P / PT` DEVEM ser exibidos como `N/A`.

#### Scenario: Fundamentus sem extremos de 52 semanas
- **WHEN** o Fundamentus não fornece a máxima e a mínima de 52 semanas e a janela da B3 em cache contém dias dentro das últimas 52 semanas
- **THEN** o sistema DEVE usar o menor mínimo e o maior máximo desses dias como `Min 52 sem` e `Max 52 sem` para calcular `Preço Típico` e `P / PT`

#### Scenario: Janela de cache vazia
- **WHEN** o Fundamentus não fornece os extremos e a janela da B3 em cache não contém dias válidos
- **THEN** `Preço Típico` e `P / PT` DEVEM ser `N/A`

#### Scenario: Extremos do Fundamentus presentes
- **WHEN** o Fundamentus fornece a máxima e a mínima de 52 semanas
- **THEN** o sistema DEVE usá-las, sem consultar a janela em cache

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

### Requirement: Fallback de dividendos e identidade de BDR

Para ativos classificados como BDR, o sistema DEVE usar a fonte de dividendos de BDR como fonte secundária de dividendos, consolidando-a com as demais fontes e preservando a origem de cada valor. Quando o último dividendo do BDR existir, o sistema DEVE usá-lo para preencher data-com, dividendo anterior, tendência, P/L e Dividend Yield. O sistema DEVE expor o caminho da pasta de cache dos PDFs do BDR e, na ausência de identidade fiscal nas fontes primárias, o depositário, a empresa e o ISIN obtidos dos avisos.

#### Scenario: BDR com dividendos na fonte secundária
- **WHEN** a B3 e o Fundamentus não fornecem dividendos para o BDR e a fonte de BDR retorna o último dividendo e a data-com
- **THEN** a análise DEVE preencher último dividendo, data-com e tendência com os valores da fonte de BDR, registrando a origem

#### Scenario: BDR sem dados em nenhuma fonte
- **WHEN** nenhuma fonte fornece dividendos para o BDR
- **THEN** as colunas de dividendo DEVEM ser `N/A`, sem impedir as demais

#### Scenario: Identidade fiscal de BDR
- **WHEN** o BDR não possui CNPJ/administrador/gestor nas fontes primárias
- **THEN** `Dados fiscais` DEVE exibir depositário, empresa e ISIN obtidos dos avisos, omitindo itens indisponíveis

#### Scenario: Caminho de cache exposto
- **WHEN** a análise de um BDR é concluída com PDFs em cache
- **THEN** `Informações adicionais` DEVE exibir o caminho da pasta de cache do ticker

#### Scenario: Ativo não-BDR preservado
- **WHEN** o ativo não é um BDR
- **THEN** a fonte de BDR NÃO DEVE ser consultada e o comportamento das fontes existentes DEVE ser mantido
