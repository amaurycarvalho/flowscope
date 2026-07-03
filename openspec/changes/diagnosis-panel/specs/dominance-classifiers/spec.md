## MODIFIED Requirements

### Requirement: Classificador de Dominância (DC301)

O sistema DEVE fornecer uma função `classify_dominance(clv: float, *, vwap_distance: float | None = None) -> DominanceClassification` que traduz o CLV em 7 níveis qualitativos, com suporte opcional a VWAP Distance para classificação enriquecida.

#### Scenario: Classificação correta para cada faixa de CLV (compatibilidade mantida)

- **WHEN** CLV está em qualquer faixa entre -1.00 e +1.00 E vwap_distance não é informado
- **THEN** a classificação DEVE ser idêntica ao comportamento anterior (mesmos thresholds e labels)

#### Scenario: Classificação enriquecida com VWAP Distance

- **WHEN** CLV > 0.15 E vwap_distance > 0
- **THEN** a classificação DEVE indicar dominância compradora confirmada (ex: "Compra Confirmada")
- **WHEN** CLV > 0.15 E vwap_distance ≤ 0
- **THEN** a classificação DEVE indicar compra em recuperação (ex: "Compra em Recuperação")
- **WHEN** CLV < -0.15 E vwap_distance < 0
- **THEN** a classificação DEVE indicar venda confirmada (ex: "Venda Confirmada")
- **WHEN** CLV < -0.15 E vwap_distance ≥ 0
- **THEN** a classificação DEVE indicar realização acima do VWAP (ex: "Realização acima do VWAP")

#### Scenario: CLV exatamente no limite

- **WHEN** CLV = −0.70
- **THEN** a classificação DEVE ser "Venda Muito Forte" (limite inferior inclusivo, superior exclusivo, exceto o último)
- **WHEN** CLV = +0.70
- **THEN** a classificação DEVE ser "Compra Muito Forte"

#### Scenario: CLV fora da faixa

- **WHEN** CLV < −1.0 ou CLV > +1.0
- **THEN** a classificação DEVE truncar para o extremo correspondente
