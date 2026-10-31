# Spec Delta

## MODIFIED Requirements

### Requirement: Dia não útil não é requisitado

A janela de datas de amostragem DEVE conter apenas dias úteis da B3 (excluindo fins de semana e feriados nacionais). O sistema NÃO DEVE requisitar o arquivo de negociação de um dia não útil e, caso uma resposta de ausência seja retornada para um dia não útil, ela DEVE ser tratada como ausência de pregão, sem registro de erro. A definição de dia útil DEVE vir do calendário dinâmico da capability `calendario-feriados`, com fallback somente-fim-de-semana quando não houver cache nem ANBIMA.

#### Scenario: Feriado excluído da janela
- **WHEN** a data de referência atravessa um feriado nacional
- **THEN** o feriado NÃO DEVE constar da janela de datas amostradas

#### Scenario: Ausência em dia não útil não é erro
- **WHEN** um arquivo de negociação é solicitado para um dia não útil e o serviço sinaliza ausência
- **THEN** o sistema DEVE tratar como ausência de pregão, sem warning de erro de download

#### Scenario: Feriado descoberto no cache ou na ANBIMA
- **WHEN** o calendário do ano está disponível no cache ou foi obtido da ANBIMA
- **THEN** o sistema usa esse calendário para decidir se a data é dia útil
- **THEN** não consulta a B3 para um feriado ausente da lista estática antiga

#### Scenario: Calendário indisponível não bloqueia a carga
- **WHEN** não há cache do ano e a ANBIMA falha
- **THEN** o sistema trata apenas sábado e domingo como não úteis
- **THEN** a carga principal continua normalmente

### Requirement: Substituição de datas sem trades (pós-resolução ticker-aware)

Após o download dos trades, cada data de amostragem DEVE ser verificada contra os dados reais dos tickers analisados. Se nenhum ticker analisado tiver negociado em uma data de amostragem, a data DEVE ser substituída pela data mais próxima (d±1..d±7, não repetida) onde pelo menos um ticker tenha negociado.

Somente **dias úteis da B3** são candidatos a substituição — segunda a sexta-feira, excluindo os feriados nacionais definidos pelo calendário dinâmico da capability `calendario-feriados`. Uma data candidata que seja fim de semana OU feriado nacional NÃO DEVE ser consultada nem usada como substituta. Essa definição de dia útil é a mesma usada no ajuste das datas de amostragem, de modo que as duas regras não divirjam.

A substituição DEVE ocorrer antes da execução do motor de indicadores, para que gráficos (ex: Evolução da Dominância) exibam todas as datas de amostragem com indicadores computados.

#### Scenario: Data de amostragem sem trades substituída
- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** d+1 possui trades de pelo menos um ticker analisado
- **THEN** o sistema DEVE substituir d por d+1 na lista de datas de amostragem
- **AND** o motor de indicadores DEVE computar indicadores para d+1

#### Scenario: Data sem trades mantida se não houver substituta
- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** nenhuma data em d±1..d±7 possui trades de nenhum ticker analisado
- **THEN** o sistema DEVE manter d na lista (como fallback, resultando em linha vazia no CSV)

#### Scenario: Candidata em feriado nacional é ignorada
- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** a data adjacente mais próxima (ex.: d-1) é um feriado nacional da B3 obtido do calendário dinâmico
- **THEN** o sistema NÃO DEVE consultar nem usar essa data como substituta
- **AND** o sistema DEVE continuar a busca pela próxima data candidata que seja dia útil da B3

#### Scenario: Calendário indisponível usa apenas fim de semana
- **WHEN** não há cache do ano e a ANBIMA falha durante a busca de substituta
- **THEN** o sistema considera não úteis apenas sábado e domingo
- **THEN** a busca continua sem bloquear a carga principal
