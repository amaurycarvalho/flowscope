## REMOVED Requirements

### Requirement: Overlay de Daily Efficiency (DT204)

**Reason**: A linha de eficiência (eixo secundário twiny + plot azul) foi removida do gráfico para simplificar a visualização. O valor de eficiência agora é exibido apenas no tooltip de cada barra, junto com a classificação de convicção.

**Migration**: Remover `twiny()`, `self._eff_line`, e todo código associado ao plot da eficiência. O valor `daily_efficiency` ainda DEVE ser carregado e armazenado em `self._hover_data` para uso no tooltip.

### Requirement: Resumo lateral (DT205)

**Reason**: O painel lateral direito (`_summary_frame` + `_summary_text`) foi removido. As informações de classificação do último pregão e KPI de pregões compradores foram redistribuídas:
- Classificação de dominância e convicção por barra → tooltip individual (DT206 expandido)
- Percentual de pregões compradores/vendedores → labels "Compradores X%" e "Vendedores Y%" no gráfico
- Total MFV do período → removido (não substituído)

**Migration**: Remover `_summary_frame`, `_summary_text`, `_update_summary()`, e todo código associado. O método `update()` não deve mais chamar `_update_summary()`. O tooltip expandido (DT206 modificado) deve cobrir a informação por barra.

## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Gráfico temporal de CLV (DT201)

O sistema DEVE exibir um gráfico de barras horizontais divergentes onde cada linha representa uma data de pregão para o ticker selecionado. O layout do gráfico DEVE ser similar ao do "Dominância do Pregão" (DominanceRankingChart), com labels nas extremidades das barras, sem painel lateral, e sem linha de eficiência sobreposta.

#### Scenario: Layout similar ao Dominância do Pregão

- **WHEN** o painel é carregado com dados de 5 pregões para PETR4
- **THEN** DEVEM ser exibidas 5 barras, uma por data, ordenadas cronologicamente da mais antiga (topo) à mais recente (base), sem painel lateral e sem linha de eficiência, com labels nas extremidades indicando a data de cada pregão

### Requirement: Codificação visual (DT202)

O sistema DEVE aplicar a mesma codificação visual do ranking (direção, comprimento, cor, espessura uniforme), com marcador representando o Money Flow diário.

#### Scenario: Tooltip substitui informação lateral

- **WHEN** o usuário passa o mouse sobre uma barra com classificação Compra Forte
- **THEN** o tooltip DEVE exibir "Dominância: Compra Forte (CLV: +0,52)" — a classificação NÃO DEVE mais aparecer em um painel lateral separado

### Requirement: Marcador de Money Flow diário (DT203)

*(Sem alterações — o marcador MFV diário via hlines permanece no chart.)*
