## Purpose

Define the Dominance Timeline panel — a time-series visualization in the Análise do Ticker tab that shows the evolution of buyer/seller dominance for a single ticker across multiple trading sessions.

## Requirements

### Requirement: Gráfico temporal de CLV (DT201)

O sistema DEVE exibir um gráfico de barras horizontais divergentes onde cada linha representa uma data de pregão para o ticker selecionado. O layout do gráfico DEVE ser similar ao do "Dominância do Pregão" (DominanceRankingChart), com labels nas extremidades das barras, sem painel lateral, e sem linha de eficiência sobreposta.

#### Scenario: Layout similar ao Dominância do Pregão

- **WHEN** o painel é carregado com dados de 5 pregões para PETR4
- **THEN** DEVEM ser exibidas 5 barras, uma por data, ordenadas cronologicamente da mais antiga (topo) à mais recente (base), sem painel lateral e sem linha de eficiência, com labels nas extremidades indicando a data de cada pregão

#### Scenario: Ordenação cronológica

- **WHEN** as datas disponíveis são 20/06, 23/06, 24/06, 25/06, 26/06
- **THEN** a barra de 20/06 DEVE estar no topo e a de 26/06 na base

### Requirement: Codificação visual (DT202)

O sistema DEVE aplicar a mesma codificação visual do ranking (direção, comprimento, cor, espessura uniforme), com marcador representando o Money Flow diário.

#### Scenario: Direção da barra

- **WHEN** CLV > 0 para uma data
- **THEN** a barra DEVE se estender para a direita
- **WHEN** CLV < 0 para uma data
- **THEN** a barra DEVE se estender para a esquerda

#### Scenario: Cor por classificação

- **WHEN** |CLV| ≥ 0.70
- **THEN** a barra DEVE usar a cor mais intensa (verde escuro / vermelho escuro)
- **WHEN** CLV entre −0.15 e +0.15
- **THEN** a barra DEVE ser cinza
- **WHEN** valores intermediários
- **THEN** a barra DEVE usar cor proporcional à magnitude

#### Scenario: Tooltip substitui informação lateral

- **WHEN** o usuário passa o mouse sobre uma barra com classificação Compra Forte
- **THEN** o tooltip DEVE exibir "Dominância: Compra Forte (CLV: +0,52)" — a classificação NÃO DEVE mais aparecer em um painel lateral separado

### Requirement: Marcador de Money Flow diário (DT203)

O sistema DEVE exibir um marcador na extremidade da barra cujo tamanho representa o Money Flow diário (CLV × FinVol daquele pregão), não o MFV acumulado.

#### Scenario: MFV diário proporcional

- **WHEN** um pregão tem CLV = 0.5 e FinVol = R$ 2M
- **THEN** o marcador DEVE corresponder a MFV_diário = R$ 1M
- **WHEN** outro pregão tem CLV = 0.5 e FinVol = R$ 200K
- **THEN** o marcador DO primeiro DEVE ser maior que o do segundo

### Requirement: Tooltip por barra (DT206)

O sistema DEVE exibir tooltip ao passar o mouse sobre cada barra com informações expandidas: Data, Dominância (label descritivo + valor do CLV), Convicção (label descritivo + eficiência como percentual), e MFV do pregão.

#### Scenario: Tooltip completo

- **WHEN** o usuário passa o mouse sobre uma barra com CLV = 0.52, eficiência = 0.45, MFV diário = R$ 480.000 na data 2025-01-10
- **THEN** o tooltip DEVE exibir:
  - Data: 2025-01-10
  - Dominância: Compra Forte (CLV: +0,52)
  - Convicção: Moderada (Efic: 45,0%)
  - MFV do pregão: R$ 480.000

*Nota: O tooltip NÃO DEVE mais exibir a linha separada de "Eficiência" (a eficiência é incorporada na linha de Convicção como percentual).*

### Requirement: Percentual de pregões nos labels (DT207)

O sistema DEVE exibir o percentual de pregões com dominância compradora e vendedora nos labels posicionados abaixo do eixo X do gráfico. Os labels substituem os atuais "Compradores →" e "← Vendedores".

#### Scenario: Labels com percentual

- **WHEN** o gráfico é renderizado com 10 pregões, dos quais 6 têm CLV > 0 e 4 têm CLV < 0
- **THEN** o label esquerdo DEVE exibir "← Vendedores 40%" e o direito "Compradores 60% →"

#### Scenario: Pregões neutros excluídos

- **WHEN** o período contém 10 pregões, com 5 compradores, 3 vendedores e 2 neutros (CLV = 0)
- **THEN** os labels DEVEM exibir "← Vendedores 37,5%" e "Compradores 62,5% →" (baseado apenas nos pregões com direção definida)

*Nota: O percentual é calculado sobre o total de pregões com direção definida (CLV ≠ 0), consistente com o comportamento do resumo lateral anterior.*

#### Scenario: Atualização dinâmica

- **WHEN** o ticker ou período analisado muda
- **THEN** os percentuais DEVEM ser recalculados e os labels atualizados

### Requirement: Tooltip acima dos stems MFV (DT208)

O tooltip DEVE ser renderizado com zorder superior ao dos stems de MFV para garantir que a caixa de tooltip não seja encoberta pelas linhas horizontais.

#### Scenario: Tooltip sobrepõe stem

- **WHEN** o usuário passa o mouse sobre uma barra que possui stem MFV
- **THEN** a caixa do tooltip DEVE aparecer sobre a linha do stem, sem ser obstruída

### Requirement: Hover em qualquer ponto da barra (DT209)

O sistema DEVE exibir o tooltip quando o mouse estiver sobre qualquer ponto da barra (entre 0 e o valor do CLV), não apenas próximo à extremidade.

#### Scenario: Hover próximo a x=0

- **WHEN** o usuário passa o mouse sobre uma barra com CLV = +0.80 na região próxima a x=0
- **THEN** o tooltip DEVE ser exibido

#### Scenario: Hover sobre stem sem barra

- **WHEN** o usuário passa o mouse sobre um stem MFV que se estende além da barra
- **THEN** o tooltip NÃO DEVE ser exibido (o stem está fora do span [0, CLV])
