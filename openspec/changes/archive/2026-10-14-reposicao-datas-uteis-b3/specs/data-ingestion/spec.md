## MODIFIED Requirements

### Requirement: Substituição de datas sem trades (pós-resolução ticker-aware)

Após o download dos trades, cada data de amostragem DEVE ser verificada contra os dados reais dos tickers analisados. Se nenhum ticker analisado tiver negociado em uma data de amostragem, a data DEVE ser substituída pela data mais próxima (d±1..d±7, não repetida) onde pelo menos um ticker tenha negociado.

Somente **dias úteis da B3** são candidatos a substituição — segunda a sexta-feira, excluindo os feriados nacionais definidos no calendário do projeto. Uma data candidata que seja fim de semana OU feriado nacional NÃO DEVE ser consultada nem usada como substituta. Essa definição de dia útil é a mesma usada no ajuste das datas de amostragem, de modo que as duas regras não divirjam.

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
- **AND** a data adjacente mais próxima (ex.: d-1) é um feriado nacional da B3
- **THEN** o sistema NÃO DEVE consultar nem usar essa data como substituta
- **AND** o sistema DEVE continuar a busca pela próxima data candidata que seja dia útil da B3
