## ADDED Requirements

### Requirement: Classificação determinística de FIAGRO

Quando a classificação determinística for acionada para um ticker com sufixo `11` que não conste da taxonomia de FIIs nem da lista de ETFs, o sistema DEVE reconhecer os FIAGROs listados na B3 e classificá-los como `FII` com sub-tipo `FIAGRO`. FIAGROs NÃO DEVEM ser elegíveis às métricas FFO. Quando o ticker não puder ser reconhecido como FIAGRO, a classificação DEVE permanecer `DESCONHECIDO`.

#### Scenario: FIAGRO reconhecido
- **WHEN** a classificação determinística é acionada para `BBGO11` e o ticker é um FIAGRO listado na B3
- **THEN** o tipo DEVE ser `FII` e o sub-tipo DEVE ser `FIAGRO`

#### Scenario: FIAGRO não é elegível ao FFO
- **WHEN** um ticker é classificado como `FII` com sub-tipo `FIAGRO`
- **THEN** a elegibilidade às métricas FFO DEVE ser falsa

#### Scenario: Ticker não reconhecido
- **WHEN** o ticker com sufixo `11` não está na taxonomia de FIIs, não é ETF e não é um FIAGRO conhecido
- **THEN** a classificação DEVE permanecer `DESCONHECIDO`, sem inferência a partir do nome

### Requirement: Sub-tipo de exibição de BDR

Quando a classificação determinística resultar em `BDR`, a exibição DEVE apresentar Tipo `Papel` e Sub-tipo `BDR`, sem inferência a partir do nome do ativo.

#### Scenario: BDR exibido como Papel/BDR
- **WHEN** a exibição é derivada de um ticker classificado como `BDR`
- **THEN** o Tipo DEVE ser `Papel` e o Sub-tipo DEVE ser `BDR`
