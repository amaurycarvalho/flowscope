## MODIFIED Requirements

### Requirement: LabelFrame para agrupamento visual
O seletor de gráfico DEVE ser agrupado em um `LabelFrame` com título "Visualização". Os botões de ação agora estão em locais separados: "Copiar Gráfico" no toolbar do chart, "Copiar Dados" na barra superior ao lado de "Carregar".

#### Scenario: Seletor agrupado
- **WHEN** a interface é renderizada
- **THEN** os radio buttons DEVEM estar dentro de um LabelFrame "Visualização"

#### Scenario: Botão Copiar Dados na barra superior
- **WHEN** a interface é renderizada sem dados carregados
- **THEN** o botão "Copiar Dados" DEVE estar na barra superior, ao lado de "Carregar", no estado desabilitado

#### Scenario: Botão Copiar Gráfico no toolbar
- **WHEN** um chart é renderizado
- **THEN** o toolbar DEVE conter um botão "Copiar Gráfico" para copiar a imagem do chart

## REMOVED Requirements

### Requirement: Separação visual entre botões de ação
**Reason**: Os botões "Copiar Dados" e "Copiar Gráfico" não estão mais lado a lado; o frame Exportação foi eliminado.
**Migration**: "Copiar Dados" está na barra superior; "Copiar Gráfico" está no toolbar do chart.
