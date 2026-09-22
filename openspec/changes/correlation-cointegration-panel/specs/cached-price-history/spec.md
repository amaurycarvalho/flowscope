## Purpose

Monta séries de preço alinhadas por ticker a partir dos caches locais do FlowScope, exclusivamente em modo somente-leitura, sem acessar a rede.

## ADDED Requirements

### Requirement: Leitura somente de cache

O sistema DEVE montar o histórico de preços usando exclusivamente arquivos já presentes nos caches locais. Nenhum download ou acesso à rede DEVE ocorrer ao abrir ou recalcular o painel. Datas ausentes do cache NÃO DEVEM ser preenchidas.

#### Scenario: Nenhum acesso à rede

- **WHEN** o histórico de preços é montado para o painel
- **THEN** nenhuma requisição de rede DEVE ser feita

#### Scenario: Datas ausentes ficam de fora

- **WHEN** uma data não está presente no cache
- **THEN** ela NÃO DEVE constar do histórico montado

### Requirement: Fonte primária no cache da B3

A fonte primária DEVE ser o cache diário da B3 (`TradeInformationConsolidated`), considerando os dias úteis disponíveis na janela escolhida e adotando o último preço do pregão como preço do dia.

#### Scenario: Série a partir do cache da B3

- **WHEN** há CSVs diários da B3 em cache na janela
- **THEN** o sistema DEVE montar a série diária de cada ticker com o último preço do pregão

#### Scenario: Janela limitada aos dias úteis

- **WHEN** a janela é informada em pregões
- **THEN** o sistema DEVE considerar apenas os dias úteis com dados em cache dentro da janela

### Requirement: Fonte alternativa no cache histórico de fundamentos

Quando o cache da B3 não fornecer densidade suficiente, o sistema DEVE poder usar a cotação do cache histórico de fundamentos como fonte alternativa. A escolha da fonte DEVE ser única para todo o painel, sem misturar fontes entre tickers na mesma execução.

#### Scenario: Fallback para fundamentos

- **WHEN** o cache da B3 não fornece observações suficientes para o painel
- **THEN** o sistema PODE montar as séries a partir da cotação do cache histórico de fundamentos

#### Scenario: Fonte única por execução

- **WHEN** uma fonte é escolhida
- **THEN** todos os tickers da execução DEVEM usar a mesma fonte

### Requirement: Cobertura e limitações reportadas

O sistema DEVE reportar a fonte utilizada, o número de datas alinhadas e as limitações de retenção aplicáveis, para que o painel comunique corretamente a disponibilidade dos dados.

#### Scenario: Reporte da cobertura

- **WHEN** o histórico é montado
- **THEN** o resultado DEVE informar a fonte, o número de datas alinhadas e a janela efetivamente coberta
