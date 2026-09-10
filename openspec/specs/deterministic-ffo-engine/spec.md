# deterministic-ffo-engine Specification

## Purpose
Cálculo determinístico, auditável e versionado do Funds From Operations (FFO) de FIIs a partir de componentes econômicos classificados, produzindo FFO mensal, 12m, por cota, FFO Yield e P/FFO, com proveniência, qualidade e reconciliação.

## Requirements

### Requirement: Classificação determinística dos componentes de resultado

O sistema DEVE classificar cada componente de resultado em exatamente um tipo — `RECURRING`, `FAIR_VALUE`, `DISPOSAL`, `NON_RECURRING` ou `UNKNOWN` — segundo regras determinísticas, sem participação de LLM no cálculo em produção. Componentes sem classificação explícita DEVEM ser tratados como `UNKNOWN` e permanecer disponíveis para auditoria.

#### Scenario: Componente recorrente
- **WHEN** um componente é explicitamente recorrente (ex.: receita de aluguel, juros de CRI)
- **THEN** o sistema DEVE classificá-lo como `RECURRING`

#### Scenario: Componente não classificável
- **WHEN** a descrição de um componente não corresponde a nenhuma regra (ex.: "Outras receitas")
- **THEN** o sistema DEVE classificá-lo como `UNKNOWN`, sem incluí-lo no FFO, preservando o valor

### Requirement: Regra de inclusão no FFO

O sistema DEVE somar ao FFO apenas os componentes `RECURRING`; `FAIR_VALUE`, `DISPOSAL` e `NON_RECURRING` DEVEM ser excluídos, e `UNKNOWN` NÃO DEVE ser incluído.

#### Scenario: FFO pela soma dos recorrentes
- **WHEN** os componentes incluem recorrentes positivos e negativos e itens de fair value/alienação
- **THEN** o FFO DEVE ser a soma dos recorrentes, excluindo os demais

### Requirement: FFO mensal, trimestral e de 12 meses

O sistema DEVE derivar o FFO mensal a partir dos componentes por competência, sem inferir meses sem base temporal/contábil suficiente, e DEVE calcular o FFO de 12 meses como a soma dos últimos 12 meses completos na janela `[reference_date - 11 meses, reference_date]`, validando a competência em vez de usar os últimos 12 registros.

#### Scenario: Janela de 12 meses validada
- **WHEN** há dados mensais de competências suficientes
- **THEN** o sistema DEVE somar exatamente as 12 competências da janela

#### Scenario: Base insuficiente
- **WHEN** faltam competências na janela
- **THEN** o sistema DEVE sinalizar a incompletude em vez de extrapolar meses

### Requirement: FFO por cota com média ponderada de cotas

O sistema DEVE calcular o FFO por cota como `FFO_12M / weighted_average_shares`, derivando a média ponderada das quantidades de cotas quando não estiver diretamente disponível.

#### Scenario: Média ponderada calculada
- **WHEN** há observações de quantidade de cotas com períodos distintos
- **THEN** o sistema DEVE calcular a média ponderada pelo tempo

### Requirement: FFO Yield e P/FFO

O sistema DEVE calcular `FFO Yield` como `FFO_por_cota / preço` (ou `FFO_12M / market_cap`) e `P/FFO` como `preço / FFO_por_cota` (ou `market_cap / FFO_12M`), usando o preço de fechamento da data de referência (ou o último pregão anterior, registrando a data do preço separadamente).

#### Scenario: Yield e múltiplo consistentes
- **WHEN** FFO por cota e preço são positivos
- **THEN** `P/FFO` DEVE ser o inverso de `FFO Yield`

#### Scenario: Preço de data anterior
- **WHEN** não há negociação na data de referência
- **THEN** o sistema DEVE usar o último pregão anterior e registrar `market_price_date`

### Requirement: Proveniência por componente

Cada componente usado no FFO DEVE registrar sua origem (fonte, dataset, arquivo, CNPJ, competência, campo, valor e classificação), permitindo explicar como o FFO foi obtido.

#### Scenario: Rastreabilidade do resultado
- **WHEN** o FFO é calculado
- **THEN** o sistema DEVE expor a proveniência de cada componente que contribuiu para o resultado

### Requirement: Qualidade do FFO

O sistema DEVE atribuir uma qualidade (`HIGH`, `MEDIUM` ou `LOW`) ao FFO com base na proporção de componentes `UNKNOWN` em relação ao resultado, segundo limites configuráveis.

#### Scenario: Materialidade dos desconhecidos
- **WHEN** a proporção de `UNKNOWN` excede o limite material
- **THEN** o sistema DEVE rebaixar a qualidade do FFO

### Requirement: Reconciliação com DFIN e Informe Trimestral

O sistema DEVE reconciliar o resultado calculado com a DFIN e o Informe Trimestral, gerando warning quando a diferença relativa exceder o limite configurável.

#### Scenario: Divergência acima do limite
- **WHEN** a diferença relativa entre o calculado e o reportado excede o limite
- **THEN** o sistema DEVE emitir warning sem descartar o resultado

### Requirement: Determinismo e versionamento

O cálculo do FFO DEVE ser determinístico e reproduzível para os mesmos dados de entrada, ser independente do ticker e do gestor, e registrar a versão do cálculo.

#### Scenario: Reprodução do resultado
- **WHEN** o cálculo é repetido com os mesmos componentes
- **THEN** o sistema DEVE produzir exatamente o mesmo FFO e a mesma qualidade

### Requirement: Integração com as métricas fundamentalistas

O FFO calculado DEVE atuar como fallback das métricas `FFO Yield`, `P/FFO` e `FFO Trend` da análise fundamentalista, sendo usado quando o Fundamentus não fornecer o dado.

#### Scenario: Métricas de FFO preenchidas
- **WHEN** o FFO 12m e o preço estão disponíveis
- **THEN** `FFO Yield` e `P/FFO` DEVEM ser calculados e exibidos

#### Scenario: FFO indisponível
- **WHEN** os componentes necessários não estão disponíveis
- **THEN** as métricas de FFO DEVEM ser exibidas como `N/A` sem impedir as demais
