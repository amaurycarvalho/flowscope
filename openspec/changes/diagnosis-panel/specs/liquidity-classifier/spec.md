## ADDED Requirements

### Requirement: Classificador de Liquidez (LC101)

O sistema DEVE fornecer uma função `classify_liquidity(financial_density: float, trade_density: float, volume_density: float) -> LiquidityClassification` que avalia a qualidade da liquidez do pregão a partir da densidade financeira, densidade de negócios e densidade de volume.

#### Scenario: Classificação retorna níveis qualitativos

- **WHEN** a função é chamada com valores de financial_density, trade_density e volume_density
- **THEN** a classificação DEVE retornar um dos níveis: "Muito Baixa", "Baixa", "Normal", "Alta", "Muito Alta"

### Requirement: Estrutura de retorno tipada (LC102)

A função DEVE retornar um objeto `LiquidityClassification` com campos label, short_label, color, score e level, para consumo direto pelos painéis.

#### Scenario: Acesso aos campos

- **WHEN** `classify_liquidity(0.8, 0.6, 0.7)` é chamada
- **THEN** o resultado DEVE conter: label, short_label, color, score e level

### Requirement: Classificador isolado sem dependência de engine (LC103)

O classificador DEVE estar em um módulo separado no pacote de classifiers, sem dependência do IndicatorEngine.

#### Scenario: Uso independente

- **WHEN** um painel importa `classify_liquidity`
- **THEN** ele DEVE poder chamá-la sem instanciar o IndicatorEngine ou carregar dados de mercado
