## Purpose

Define the classifiers that translate quantitative indicator values into qualitative business language — separating dominance (CLV-based) from conviction (Daily Efficiency-based).

## Requirements

### Requirement: Classificador de Dominância (DC301)

O sistema DEVE fornecer uma função `classify_dominance(clv: float) -> DominanceClassification` que traduz o CLV em 7 níveis qualitativos, sem considerar nenhum outro indicador.

#### Scenario: Classificação correta para cada faixa de CLV

- **WHEN** CLV entre −1.00 e −0.70
- **THEN** a classificação DEVE ser "Venda Muito Forte" com score numérico −3
- **WHEN** CLV entre −0.70 e −0.40
- **THEN** a classificação DEVE ser "Venda Forte" com score −2
- **WHEN** CLV entre −0.40 e −0.15
- **THEN** a classificação DEVE ser "Venda Moderada" com score −1
- **WHEN** CLV entre −0.15 e +0.15
- **THEN** a classificação DEVE ser "Equilíbrio" com score 0
- **WHEN** CLV entre +0.15 e +0.40
- **THEN** a classificação DEVE ser "Compra Moderada" com score +1
- **WHEN** CLV entre +0.40 e +0.70
- **THEN** a classificação DEVE ser "Compra Forte" com score +2
- **WHEN** CLV entre +0.70 e +1.00
- **THEN** a classificação DEVE ser "Compra Muito Forte" com score +3

#### Scenario: CLV exatamente no limite

- **WHEN** CLV = −0.70
- **THEN** a classificação DEVE ser "Venda Muito Forte" (limite inferior inclusivo, superior exclusivo, exceto o último)
- **WHEN** CLV = +0.70
- **THEN** a classificação DEVE ser "Compra Muito Forte"

#### Scenario: CLV fora da faixa

- **WHEN** CLV < −1.0 ou CLV > +1.0
- **THEN** a classificação DEVE truncar para o extremo correspondente

### Requirement: Estrutura de retorno tipada (DC302)

A função DEVE retornar um objeto `DominanceClassification` com campos label, short_label, color e score, para consumo direto pelos painéis.

#### Scenario: Acesso aos campos

- **WHEN** `classify_dominance(0.55)` é chamada
- **THEN** o resultado DEVE conter: label = "Compra Forte", short_label = "Forte", color = "#2E7D32", score = 2

### Requirement: Classificador de Convicção (DC303)

O sistema DEVE fornecer uma função `classify_conviction(efficiency: float) -> ConvictionClassification` que traduz a Daily Efficiency em 5 níveis qualitativos.

#### Scenario: Classificação correta para cada faixa de eficiência

- **WHEN** efficiency ≥ 0.80
- **THEN** a classificação DEVE ser "Muito Alta" com score +2
- **WHEN** 0.60 ≤ efficiency < 0.80
- **THEN** a classificação DEVE ser "Alta" com score +1
- **WHEN** 0.40 ≤ efficiency < 0.60
- **THEN** a classificação DEVE ser "Moderada" com score 0
- **WHEN** 0.20 ≤ efficiency < 0.40
- **THEN** a classificação DEVE ser "Baixa" com score −1
- **WHEN** efficiency < 0.20
- **THEN** a classificação DEVE ser "Muito Baixa" com score −2

### Requirement: Separação entre cálculo e classificação (DC304)

Os classificadores DEVEM estar em um módulo distinto das strategies de cálculo, sem dependência do engine de indicadores.

#### Scenario: Uso independente

- **WHEN** um painel importa `classify_dominance`
- **THEN** ele DEVE poder chamá-la sem precisar instanciar o IndicatorEngine ou carregar dados de mercado
