## ADDED Requirements

### Requirement: Recarga da mesma data reutiliza o cache histórico

Ao carregar dados para uma watchlist, o sistema DEVE reutilizar o cache histórico de resultados fundamentalistas por `(ticker, data)`, de modo que tickers já analisados para a data solicitada sejam exibidos na sub-aba "Fundamentos" sem refazer a aquisição, e os resultados exibidos correspondam sempre à data da carga corrente.

#### Scenario: Recarga da mesma data é instantânea

- **WHEN** o usuário recarrega dados para uma data já analisada anteriormente
- **THEN** a sub-aba "Fundamentos" DEVE ser populada a partir do cache histórico, sem nova aquisição para os tickers já observados naquela data

#### Scenario: Resultados não vazam entre datas

- **WHEN** o usuário carrega dados para uma data diferente da carga anterior
- **THEN** a tabela DEVE exibir apenas observações da data corrente, não reaproveitando linhas de outra data

#### Scenario: Ticker novo na data completa o restante

- **WHEN** a watchlist inclui um ticker ainda não observado para a data solicitada
- **THEN** o sistema DEVE analisar apenas esse ticker e combinar o resultado com os demais servidos pelo cache

### Requirement: Bypass explícito do cache histórico na interface

A sub-aba "Fundamentos" DEVE oferecer uma ação explícita para ignorar o cache histórico e forçar a recomputação da data corrente, sobrescrevendo as observações do dia.

#### Scenario: Atualização forçada no mesmo dia

- **WHEN** o usuário aciona a ação de atualização forçada com uma data carregada
- **THEN** o sistema DEVE recomputar a análise dos tickers exibidos, substituindo as observações do dia, independentemente de já existirem
