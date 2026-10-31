# Spec Delta

## Purpose

Manter um calendário interno de dias úteis alimentado pela ANBIMA, com cache, fallback, resolução de datas e exportação, para que cargas, TTLs e exibições não usem feriados como datas de negociação.

## ADDED Requirements

### Requirement: Fonte ANBIMA por ano

O sistema DEVE obter os feriados da página anual da ANBIMA (`feriados/fer_nacionais/{ano}.asp`) e DEVE registrar a URL, o ano, o instante de extração e a origem em cada leitura. Cada feriado DEVE registrar sua origem individual (`ANBIMA` ou recesso local da B3). NÃO DEVE existir uma segunda fonte de rede para feriados.

#### Scenario: Ano é carregado da ANBIMA
- **WHEN** o calendário do ano corrente é atualizado e a ANBIMA responde com a tabela de feriados
- **THEN** o sistema grava os feriados normalizados com origem individual `ANBIMA`
- **THEN** o payload registra a URL, o instante de extração e a origem do ano

#### Scenario: Falha da ANBIMA não troca de fonte
- **WHEN** a ANBIMA responde com erro, timeout ou página inesperada
- **THEN** o sistema NÃO DEVE consultar outra fonte de rede
- **THEN** aplica o fallback definido para cache anterior

### Requirement: Normalização e validação dos feriados

O sistema DEVE normalizar datas `d/m/aa` para ISO (`AAAA-MM-DD`), DEVE remover acentos e entidades HTML do nome e DEVE validar que o dia da semana informado corresponde à data. Uma linha inválida DEVE invalidar a carga do ano, sem produzir calendário parcial.

#### Scenario: Data é normalizada
- **WHEN** a ANBIMA informa `1/1/26`
- **THEN** o feriado é armazenado como `2026-01-01`

#### Scenario: Dia da semana divergente
- **WHEN** o dia da semana declarado não corresponde à data calculada
- **THEN** o sistema trata a carga como falha de fonte
- **THEN** NÃO DEVE gravar um calendário parcial

### Requirement: Cache por ano com TTL por recência

O sistema DEVE manter um arquivo por ano com os feriados, o TTL aplicado e os metadados de origem. Anos passados DEVEM ser imutáveis por expiração automática, mas podem ser revalidados por atualização forçada explícita; o ano corrente e anos futuros DEVEM usar TTL curto; ano futuro ainda não publicado DEVE usar cache negativo com TTL.

#### Scenario: Cache fresco evita nova carga
- **WHEN** o arquivo do ano existe, é válido e está dentro do TTL
- **THEN** o sistema reutiliza o cache sem acessar a ANBIMA

#### Scenario: Cache do ano corrente expira
- **WHEN** o arquivo do ano corrente está além do TTL curto
- **THEN** a próxima carga de dados DEVE revalidar o ano na ANBIMA

#### Scenario: Ano futuro ainda não publicado
- **WHEN** a ANBIMA não publica o ano futuro solicitado, seja por ausência de página ou por página sem tabela de feriados
- **THEN** o sistema grava um marcador negativo com TTL
- **THEN** o estado exposto é `calendario_indisponivel`
- **THEN** novas cargas NÃO DEVEM consultar o mesmo ano antes do TTL

### Requirement: Fallback para cache anterior e modo degradado

Quando a ANBIMA falhar, o sistema DEVE reutilizar o cache anterior do ano, marcado como defasado. Sem cache algum para o ano, o sistema DEVE aplicar apenas a regra de fim de semana e DEVE expor o estado `calendario_indisponivel`.

#### Scenario: Falha usa cache anterior
- **WHEN** a ANBIMA falha e existe cache anterior para o ano
- **THEN** o sistema usa o cache anterior
- **THEN** o estado do calendário é marcado como defasado

#### Scenario: Sem cache, fim de semana apenas
- **WHEN** a ANBIMA falha e não existe cache para o ano
- **THEN** o sistema trata sábado e domingo como não úteis
- **THEN** o estado do calendário é `calendario_indisponivel`
- **THEN** a carga de dados NÃO DEVE ser bloqueada

### Requirement: Housekeeping de três anos

O sistema DEVE remover arquivos de anos fora do intervalo `[ano_corrente - 3, ano_corrente + 1]` após uma atualização bem-sucedida, usando o ano corrente no fuso local. O housekeeping NUNCA DEVE remover o ano usado pela operação corrente e DEVE ignorar arquivos corrompidos.

#### Scenario: Anos antigos são removidos
- **WHEN** o ano corrente é 2026 e existe arquivo de 2021
- **THEN** o housekeeping remove o arquivo de 2021
- **THEN** mantém 2023, 2024, 2025, 2026 e 2027

#### Scenario: Ano da operação é protegido
- **WHEN** a operação corrente usa um ano fora da janela de retenção
- **THEN** esse ano NÃO é removido durante a operação
- **THEN** os demais anos fora da janela são removidos normalmente

#### Scenario: Corrupção não interrompe a limpeza
- **WHEN** um arquivo de ano não pode ser lido
- **THEN** o housekeeping o ignora e continua os demais

### Requirement: Recesso local da B3

Além dos feriados publicados pela ANBIMA, o sistema DEVE tratar 24 de dezembro e 31 de dezembro como não úteis quando caírem em dia de semana e não constarem da página da ANBIMA, registrando a origem como regra local da B3. Essa regra NÃO DEVE ser uma fonte de rede.

#### Scenario: Véspera de Natal em dia de semana
- **WHEN** 24 de dezembro do ano consultado é dia de semana e não está na ANBIMA
- **THEN** a data é tratada como não útil com a origem de recesso local da B3

#### Scenario: Recesso coincide com feriado da ANBIMA
- **WHEN** 24 ou 31 de dezembro já consta na página da ANBIMA
- **THEN** o feriado é gravado uma única vez com a origem `ANBIMA`

### Requirement: Resolução de dia útil

O sistema DEVE expor uma resolução que devolve a data informada quando ela é dia útil, ou o dia útil anterior quando é fim de semana ou feriado. A resolução DEVE informar `data_solicitada`, `data_resolvida`, `ajustada`, `motivo` e, quando aplicável, o nome e a origem do feriado.

#### Scenario: Fim de semana retrocede
- **WHEN** a data solicitada é sábado ou domingo
- **THEN** a resolução devolve a sexta-feira anterior
- **THEN** `motivo` é `fim_de_semana`

#### Scenario: Feriado retrocede
- **WHEN** a data solicitada é feriado em dia de semana
- **THEN** a resolução devolve o dia útil anterior
- **THEN** `motivo` é `feriado` e o nome do feriado é informado

#### Scenario: Bloco de feriados atravessa dias consecutivos
- **WHEN** a data solicitada e os dias anteriores formam um bloco de feriados
- **THEN** a resolução retrocede até o primeiro dia útil anterior ao bloco

#### Scenario: Bloco de feriados atravessa a virada do ano
- **WHEN** a data solicitada está nos primeiros dias de janeiro e o fim de dezembro do ano anterior forma um bloco de feriados
- **THEN** o sistema consulta o calendário do ano anterior, garantindo-o quando necessário
- **THEN** a resolução retrocede até o primeiro dia útil anterior ao bloco

#### Scenario: Dia útil é preservado
- **WHEN** a data solicitada é dia útil
- **THEN** a resolução devolve a própria data com `ajustada` falso

### Requirement: Data corrente no fuso local

O sistema DEVE determinar a data corrente, o ano corrente e a data de referência padrão no fuso local do processo, e NÃO DEVE usar a data em UTC para essas finalidades.

#### Scenario: Virada de dia no fuso local
- **WHEN** o instante local já pertence ao dia seguinte enquanto o instante UTC ainda pertence ao dia anterior
- **THEN** o sistema usa a data local para o botão de data atual, para o ano corrente do calendário e para os TTLs por recência

### Requirement: Atualização junto das cargas

As cargas de dados existentes DEVEM garantir o calendário do ano da data de referência antes de resolver a data. A atualização DEVE ser best-effort, com lock e TTL, e uma falha do calendário NÃO DEVE impedir a carga principal.

#### Scenario: Carga atualiza o calendário antes de resolver
- **WHEN** uma carga de dados é iniciada
- **THEN** o sistema garante o calendário do ano da data de referência
- **THEN** só depois resolve a data e consulta a fonte de dados

#### Scenario: Falha do calendário não bloqueia
- **WHEN** a atualização do calendário falha
- **THEN** a carga principal continua com o cache anterior ou com a regra de fim de semana
- **THEN** a falha é registrada em log

### Requirement: Resolução da data de referência

A data de referência de uma carga DEVE ser resolvida para o dia útil anterior quando cair em fim de semana ou feriado. A amostragem de datas mantém o contrato de ajuste para o próximo dia útil definido em `sampling-strategy`.

#### Scenario: Referência em feriado
- **WHEN** a data de referência informada é feriado em dia de semana
- **THEN** a carga usa o dia útil anterior como data-base
- **THEN** a data solicitada e a data resolvida são registradas no resultado

#### Scenario: Amostragem preservada
- **WHEN** a data de referência é resolvida para o dia útil anterior
- **THEN** os alvos de amostragem continuam sendo ajustados para o próximo dia útil
- **THEN** datas duplicadas permanecem colapsadas em uma única entrada

### Requirement: Atualização forçada

O sistema DEVE permitir forçar a revalidação de um ano, ignorando o TTL. Uma falha na atualização forçada DEVE preservar o cache anterior e expor o estado defasado.

#### Scenario: Revalidação bem-sucedida
- **WHEN** a atualização forçada de um ano é solicitada
- **THEN** o sistema consulta a ANBIMA mesmo com cache fresco
- **THEN** o cache é substituído pelos dados novos

#### Scenario: Falha preserva o cache
- **WHEN** a atualização forçada falha e existe cache anterior
- **THEN** o cache anterior permanece disponível
- **THEN** o estado do calendário é marcado como defasado

### Requirement: Concorrência e escrita atômica

A gravação do cache do calendário DEVE ser atômica e protegida por lock dedicado. Leituras somente de cache NÃO DEVEM gravar, renomear ou remover arquivos.

#### Scenario: Cargas concorrentes usam o mesmo cache
- **WHEN** duas cargas tentam atualizar o mesmo ano ao mesmo tempo
- **THEN** o lock evita gravação concorrente
- **THEN** a segunda carga reutiliza o resultado da primeira

#### Scenario: Leitura não altera o cache
- **WHEN** a CLI, o MCP ou a GUI lê o calendário em modo somente cache
- **THEN** nenhum arquivo do calendário é criado, alterado ou removido

### Requirement: Consulta e exportação do calendário

O sistema DEVE expor os feriados de um ano e a classificação de uma data como dia útil ou não, com nome, motivo e origem. A exportação DEVE suportar CSV e JSON como conteúdo, sem gravar arquivos no servidor MCP.

#### Scenario: Listagem do ano
- **WHEN** o usuário lista os feriados de 2026
- **THEN** cada item contém data, dia da semana, nome e origem

#### Scenario: Consulta de uma data
- **WHEN** o usuário consulta uma data
- **THEN** a resposta informa se é dia útil e, quando não for, o motivo e o nome do feriado

#### Scenario: Exportação CSV
- **WHEN** o usuário exporta o ano em CSV
- **THEN** o artefato usa `;` como separador, datas ISO e colunas de data, dia da semana, nome e origem

#### Scenario: Exportação JSON
- **WHEN** o usuário exporta o ano em JSON
- **THEN** o artefato contém o ano, a origem, o instante de extração, o estado do calendário e a lista de feriados
