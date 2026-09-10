## MODIFIED Requirements

### Requirement: Extração de dados fundamentalistas por ticker

O sistema DEVE obter os dados de um ticker a partir de `detalhes.php?papel={TICKER}` e retornar um modelo tipado com identidade (ticker, nome, discriminador do rótulo de ticker `Papel`/`FII`, espécie `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`), cotação e data da última cotação, oscilações, indicadores, balanço, demonstrativos de 12 e 3 meses e, para FIIs, dados de imóveis e composição de ativos.

#### Scenario: Dados de uma ação
- **WHEN** o ticker é uma ação válida
- **THEN** o sistema DEVE retornar o modelo com discriminador `Papel`, `Tipo` (espécie), `Setor` e `Subsetor` preenchidos quando presentes

#### Scenario: Dados de um FII
- **WHEN** o ticker é um FII válido
- **THEN** o sistema DEVE retornar o modelo com discriminador `FII`, `Segmento`, `Gestão` e `Qtd imóveis` preenchidos quando presentes

### Requirement: Detecção automática do tipo de ativo

O sistema DEVE identificar automaticamente se o ticker é FII ou ação a partir do rótulo do campo de ticker (`Papel` ou `FII`) presente na página, sem exigir configuração do chamador.

#### Scenario: Layout de FII reconhecido
- **WHEN** o campo do ticker tem rótulo `FII`
- **THEN** o sistema DEVE classificar o ativo como FII

#### Scenario: Layout de ação reconhecido
- **WHEN** o campo do ticker tem rótulo `Papel`
- **THEN** o sistema DEVE classificar o ativo como ação (não-FII)

## ADDED Requirements

### Requirement: Balizador Tijolo/Papel por Qtd imóveis

O sistema DEVE expor o campo `Qtd imóveis` do bloco de imóveis para que o consumidor determine se um FII é de tijolo (`Qtd imóveis > 0`) ou de papel (`Qtd imóveis` ausente ou igual a zero).

#### Scenario: FII de tijolo
- **WHEN** o FII possui `Qtd imóveis` maior que zero
- **THEN** o campo DEVE indicar quantidade positiva de imóveis

#### Scenario: FII de papel
- **WHEN** o FII possui `Qtd imóveis` igual a zero ou ausente
- **THEN** o campo DEVE indicar zero ou ausência
