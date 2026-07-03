## ADDED Requirements

### Requirement: Classificador Institucional (IC101)

O sistema DEVE fornecer uma função `classify_institutional(avg_trade_size: float, avg_financial_ticket: float) -> InstitutionalClassification` que estima o perfil dos participantes do pregão (institucional vs. varejo) a partir do tamanho médio dos negócios e do ticket financeiro médio.

#### Scenario: Classificação retorna níveis qualitativos

- **WHEN** a função é chamada com valores de avg_trade_size e avg_financial_ticket
- **THEN** a classificação DEVE retornar um dos níveis: "Varejo", "Misto", "Institucional", "Institucional Forte"

### Requirement: Estrutura de retorno tipada (IC102)

A função DEVE retornar um objeto `InstitutionalClassification` com campos label, short_label, color, score e level, para consumo direto pelos painéis.

#### Scenario: Acesso aos campos

- **WHEN** `classify_institutional(5000, 15000)` é chamada
- **THEN** o resultado DEVE conter: label, short_label, color, score e level

### Requirement: Classificador isolado sem dependência de engine (IC103)

O classificador DEVE estar em um módulo separado no pacote de classifiers, sem dependência do IndicatorEngine.

#### Scenario: Uso independente

- **WHEN** um painel importa `classify_institutional`
- **THEN** ele DEVE poder chamá-la sem instanciar o IndicatorEngine ou carregar dados de mercado
