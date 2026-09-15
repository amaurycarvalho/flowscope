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

A sub-aba "Fundamentos" DEVE oferecer uma ação explícita para ignorar o cache histórico e forçar a recomputação da data corrente, sobrescrevendo as observações do dia. A ação DEVE ser apresentada como um botão da barra da lista de tickers, DEVE ser exibida apenas enquanto a sub-aba "Fundamentos" estiver ativa e DEVE permanecer desabilitada enquanto houver uma carga de dados em andamento.

#### Scenario: Atualização forçada no mesmo dia

- **WHEN** o usuário aciona a ação de atualização forçada com uma data carregada
- **THEN** o sistema DEVE recomputar a análise dos tickers exibidos, substituindo as observações do dia, independentemente de já existirem

#### Scenario: Ação visível apenas na sub-aba Fundamentos

- **WHEN** a sub-aba ativa não é "Fundamentos"
- **THEN** a ação de atualização forçada NÃO DEVE ser exibida

#### Scenario: Ação desabilitada durante a carga

- **WHEN** uma carga de dados está em andamento
- **THEN** a ação de atualização forçada DEVE permanecer desabilitada

### Requirement: Tooltips descritivos dos botões de índice

Os botões de índice IBOV, IDIV e IFIX DEVEM exibir, ao passar o mouse, um tooltip curto com apenas a descrição do índice correspondente.

#### Scenario: Tooltip de cada índice

- **WHEN** o usuário posiciona o mouse sobre o botão de um índice
- **THEN** o sistema DEVE exibir a descrição correspondente — `IBOV`: "principais ações negociadas na B3"; `IDIV`: "ações com os maiores dividendos da B3"; `IFIX`: "principais fundos imobiliários (FIIs)"
