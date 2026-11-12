## MODIFIED Requirements

### Requirement: Ledger de avaliação de guidance por RG

O sistema DEVE persistir, por FII, um ledger em `~/.cache/flowscope/guidance/<TICKER>.json` com uma entrada por Relatório Gerencial avaliado, identificada pelo hash SHA-256 do conteúdo do PDF. Cada entrada DEVE registrar o método da avaliação (`ia` ou `deterministico`), a data do relatório de origem, o caminho do PDF, o resultado — um guidance com valor mínimo, valor máximo e período, ou a ausência de guidance — e a proveniência da avaliação: `avaliado_em`, versão do prompt e, quando disponível, o modelo utilizado. A escrita DEVE ser atômica e a leitura DEVE tolerar arquivo ausente, corrompido, sem os campos de proveniência ou no formato v1 (guidance único, sem hash nem origem), tratando o formato v1 como uma entrada `deterministico`. Entrada sem `prompt_version` DEVE ser considerada desatualizada para fins de reavaliação. Documento sem hash disponível DEVE usar o caminho relativo do arquivo como identidade substituta.

#### Scenario: FII sem guidance conhecido
- **WHEN** um FII nunca teve nenhuma entrada de guidance avaliada
- **THEN** a leitura DEVE resultar em ledger vazio, sem erro

#### Scenario: Guidance recuperado entre execuções
- **WHEN** uma avaliação é gravada no ledger e lida novamente
- **THEN** o método, a data do relatório, o caminho do PDF e o resultado DEVEM ser recuperados da entrada do RG

#### Scenario: Proveniência da avaliação recuperada
- **WHEN** uma avaliação por IA é gravada e lida novamente
- **THEN** o momento da avaliação, a versão do prompt e o modelo utilizado DEVEM ser recuperados da entrada

#### Scenario: Cache corrompido
- **WHEN** o arquivo de ledger do ticker contém JSON inválido
- **THEN** a leitura DEVE ser tolerada como ledger vazio, sem erro

#### Scenario: Migração do formato v1
- **WHEN** o arquivo do ticker está no formato v1, com um guidance único sem hash nem origem
- **THEN** o sistema DEVE lê-lo como uma entrada `deterministico`, preservando o guidance exposto até a próxima avaliação

#### Scenario: Entrada antiga sem proveniência
- **WHEN** uma entrada do ledger não possui versão de prompt ou momento de avaliação
- **THEN** a leitura DEVE preservar o resultado existente e tratá-la como desatualizada para reavaliação

#### Scenario: Documento sem hash
- **WHEN** o documento avaliado ainda não possui hash de conteúdo registrado
- **THEN** o sistema DEVE usar o caminho relativo do arquivo como identidade da entrada

### Requirement: Avaliação uma vez por método

Para cada Relatório Gerencial, o sistema DEVE avaliar no máximo uma vez por método e por versão de avaliação. Quando a entrada do RG no ledger estiver marcada como `ia` com a versão de prompt e o modelo atuais, nenhuma nova avaliação DEVE ocorrer. Quando estiver marcada como `ia` com versão de prompt ou modelo anterior, ou sem esses dados, o sistema DEVE reavaliá-la pela IA e substituir a entrada quando a IA estiver disponível. Quando estiver marcada como `deterministico` e a IA estiver disponível, o sistema DEVE avaliar pela IA e substituir a entrada (a IA prevalece sobre o determinístico). Quando estiver marcada como `deterministico` e a IA não estiver disponível, nenhuma nova avaliação DEVE ocorrer. Uma falha na interação com a IA NÃO DEVE marcar a entrada como `ia`, DEVE preservar o resultado anterior e DEVE ser registrada de modo que a decisão de pendência seguinte distinga "IA tentou e falhou" de "IA nunca tentou". Uma entrada determinística com falha de interação registrada NÃO DEVE manter o botão "Resumir pendentes" habilitado indefinidamente; o RG volta a ser acionável quando a avaliação for autorizada novamente (por reconfiguração da IA, por uma nova sessão de uso, ou quando uma nova avaliação por IA concluir com sucesso).

#### Scenario: RG já avaliado por IA não é reavaliado
- **WHEN** a entrada do RG está marcada como `ia` com a versão de prompt e o modelo atuais e o documento é processado novamente
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: RG com IA de versão anterior é reavaliado
- **WHEN** a entrada do RG está marcada como `ia` com versão de prompt ou modelo diferente da atual
- **THEN** o sistema DEVE avaliar novamente pela IA e substituir a entrada com a proveniência atual

#### Scenario: Entrada sem versão é reavaliada
- **WHEN** a entrada do RG está marcada como `ia` sem `prompt_version` ou momento de avaliação e a IA está disponível
- **THEN** o sistema DEVE reavaliá-la pela IA e gravar a proveniência atual

#### Scenario: Falha na reavaliação preserva a entrada anterior
- **WHEN** a reavaliação por IA de uma entrada antiga falha
- **THEN** o sistema DEVE manter o resultado anterior e registrar a falha, sem marcar a entrada como atual

#### Scenario: RG determinístico é reavaliado pela IA quando disponível
- **WHEN** a entrada do RG está marcada como `deterministico`, a IA está funcional e não há falha de interação registrada
- **THEN** o sistema DEVE avaliar pela IA e substituir a entrada do RG, prevalecendo a IA

#### Scenario: RG determinístico não é reavaliado sem IA
- **WHEN** a entrada do RG está marcada como `deterministico` e a IA não está disponível
- **THEN** o sistema NÃO DEVE avaliar nem alterar o ledger do RG

#### Scenario: Falha da IA preserva a entrada e permite nova tentativa
- **WHEN** a interação com a IA falha ao avaliar um RG
- **THEN** a entrada NÃO DEVE ser marcada como `ia`, DEVE manter o resultado determinístico e DEVE registrar a falha da interação, distinguindo-a de "IA nunca tentou"

#### Scenario: Falha repetida não mantém a pendência acionável
- **WHEN** a avalição por IA de um RG determinístico falhou e o usuário reexecuta "Resumir pendentes" sem que a IA tenha se recuperado
- **THEN** o RG NÃO DEVE contar como pendência acionável que mantenha o botão habilitado

#### Scenario: RG volta a ser acionável quando a IA se recupera
- **WHEN** a IA volta a responder com sucesso para um RG cuja entrada estava determinística com falha registrada
- **THEN** o sistema DEVE substituir a entrada pela avaliação por IA

#### Scenario: Reconfiguração da IA reabilita a avaliação
- **WHEN** o usuário reconfigura o provedor de IA e há RG determinístico com falha registrada
- **THEN** o RG DEVE voltar a ser acionável para nova avaliação por IA

### Requirement: Derivação do guidance corrente

O guidance exposto à análise fundamentalista DEVE ser derivado do ledger, selecionando a entrada com resultado de guidance e maior `data_relatorio`. Quando houver mais de uma entrada com a mesma `data_relatorio`, o desempate DEVE preferir o método `ia` sobre `deterministico` e, dentro do mesmo método, a avaliação mais recente por `avaliado_em`. Entradas cujo resultado seja ausência de guidance NÃO DEVEM remover o guidance corrente apontado por outro RG. Sem nenhuma entrada com resultado de guidance, o FII DEVE ser tratado como sem guidance.

#### Scenario: Entrada mais recente vence
- **WHEN** o ledger possui guidance em `2026/07` e em `2026/08`
- **THEN** o guidance derivado DEVE ser o de `2026/08`

#### Scenario: Mesma data, IA prevalece sobre determinístico
- **WHEN** o ledger possui, para a mesma data, uma entrada `deterministico` e uma entrada `ia` com guidance
- **THEN** o guidance derivado DEVE ser o da entrada `ia`

#### Scenario: Mesma data e mesmo método, avaliação mais recente prevalece
- **WHEN** o ledger possui duas entradas `ia` com a mesma data de relatório e momentos de avaliação diferentes
- **THEN** o guidance derivado DEVE ser o da avaliação mais recente

#### Scenario: Ausência recente não apaga guidance anterior
- **WHEN** a entrada mais recente do ledger registra ausência de guidance e uma entrada anterior registra guidance
- **THEN** o guidance derivado DEVE ser o da entrada anterior

#### Scenario: Ledger sem guidance
- **WHEN** nenhuma entrada do ledger registra guidance
- **THEN** o FII DEVE ser tratado como sem guidance

### Requirement: Formato e regras da resposta da avaliação pela IA

O prefixo de sistema DEVE exigir a resposta em quatro linhas, nesta ordem: `GUIDANCE: SIM ou NAO`, `VALOR_MIN: <valor por cota ou vazio>`, `VALOR_MAX: <valor por cota ou vazio>` e `PERIODO: <período ou vazio>`. O prompt DEVE ainda definir que, com `GUIDANCE: NAO`, os campos de valor e período ficam vazios; que um valor único preenche mínimo e máximo com o mesmo número; que o separador decimal é o ponto, sem símbolo de moeda; e que, na dúvida, deve-se responder `NAO`. A interpretação da resposta DEVE tolerar símbolo de moeda, separador de milhar, faixa na mesma linha e sufixo por cota; uma resposta `GUIDANCE: SIM` sem nenhum valor interpretável DEVE ser tratada como falha da IA, acionando a extração determinística. O período DEVE ser normalizado, convertendo valores vagos em ausência de período.

#### Scenario: Saída vazia quando não há guidance
- **WHEN** o trecho não contém guidance de distribuição
- **THEN** o prefixo DEVE exigir `GUIDANCE: NAO` com `VALOR_MIN`, `VALOR_MAX` e `PERIODO` vazios

#### Scenario: Valor único replica em mínimo e máximo
- **WHEN** o trecho projeta um único valor por cota
- **THEN** o prefixo DEVE exigir que `VALOR_MIN` e `VALOR_MAX` recebam o mesmo número

#### Scenario: Separador decimal sem símbolo
- **WHEN** o trecho projeta um valor por cota
- **THEN** o prefixo DEVE exigir ponto como separador decimal e vedar símbolos de moeda

#### Scenario: Símbolo de moeda é tolerado na resposta
- **WHEN** a IA responde `GUIDANCE: SIM` com `VALOR_MIN: R$ 0,85` e `VALOR_MAX: R$ 0,90`
- **THEN** o sistema DEVE interpretar os valores `0,85` e `0,90`, sem descartar a resposta

#### Scenario: Faixa na mesma linha é tolerada
- **WHEN** a IA responde `VALOR_MIN: 0,85 a 0,90` e deixa `VALOR_MAX` vazio
- **THEN** o sistema DEVE interpretar mínimo `0,85` e máximo `0,90`

#### Scenario: SIM sem valores aciona o determinístico
- **WHEN** a IA responde `GUIDANCE: SIM` sem nenhum valor interpretável
- **THEN** o sistema DEVE tratar a resposta como falha da IA e recorrer à extração determinística, sem registrar ausência por IA

#### Scenario: Período vago é normalizado
- **WHEN** a IA responde com período `não especificado`, `sem período` ou `N/A`
- **THEN** o sistema DEVE registrar o guidance sem período, em vez de manter o texto vago

## ADDED Requirements

### Requirement: Registro de conflito entre IA e extração determinística

Quando a IA concluir ausência de guidance em todas as fontes, o sistema DEVE executar a extração determinística apenas para diagnóstico e, se ela encontrar guidance, DEVE registrar um aviso de conflito com ticker, data do relatório, valores e período, sem alterar automaticamente o resultado da IA nem o ledger.

#### Scenario: Conflito registrado sem sobrescrever a IA
- **WHEN** a IA conclui ausência em todas as fontes e o extrator determinístico encontra guidance
- **THEN** o sistema DEVE registrar o conflito em log e manter a ausência avaliada pela IA

#### Scenario: Sem conflito nada é registrado
- **WHEN** a IA e o extrator determinístico concordam com a ausência
- **THEN** o sistema NÃO DEVE registrar aviso de conflito
