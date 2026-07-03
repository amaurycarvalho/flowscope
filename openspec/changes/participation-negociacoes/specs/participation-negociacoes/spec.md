## ADDED Requirements

### Requirement: Painel exibe Índice de Concentração das Negociações

O sistema DEVE exibir um painel visual na tab "Participação nas Negociações" contendo:
- Gauge horizontal do Índice de Concentração (score 0 a 1 combinando ATS + AFT)
- Card com Average Financial Ticket (R$) e Average Trade Size (ações/negócio)
- Timeline da evolução do Average Financial Ticket nos pregões disponíveis
- Classificação qualitativa do grau de concentração

#### Scenario: Gauge mostra score normalizado

- **WHEN** o usuário seleciona um ticker com dados históricos suficientes (≥3 pregões)
- **THEN** o gauge DEVE exibir um marcador na posição correspondente ao score de concentração, com a escala variando de "Fragmentado" (esquerda) a "Concentrado" (direita)

#### Scenario: Card exibe valores do pregão atual

- **WHEN** o painel é atualizado com dados de um ticker
- **THEN** o card DEVE exibir o Average Financial Ticket do pregão mais recente em formato R$, o Average Trade Size em ações/negócio, e a variação percentual de cada um em relação à mediana histórica do período

#### Scenario: Timeline mostra histórico do AFT

- **WHEN** o painel é atualizado com dados de um ticker
- **THEN** a timeline DEVE exibir uma linha do Average Financial Ticket ao longo dos pregões disponíveis, com uma linha horizontal representando a mediana do período

### Requirement: Classificação qualitativa por z-score

O sistema DEVE classificar o grau de concentração das negociações utilizando z-score dos indicadores ATS e AFT em relação ao histórico do próprio ticker.

#### Scenario: Classificação Muito Concentrado

- **WHEN** o z-score combinado (ATS + AFT) é maior que 1.5
- **THEN** o sistema DEVE exibir a classificação "Muito Concentrado" e o texto "As negociações ocorreram em blocos significativamente maiores que o habitual para este ativo. Esse comportamento é compatível com maior participação de investidores de grande porte."

#### Scenario: Classificação Concentrado

- **WHEN** o z-score combinado está entre 0.8 e 1.5
- **THEN** o sistema DEVE exibir a classificação "Concentrado"

#### Scenario: Classificação Equilibrado

- **WHEN** o z-score combinado está entre -0.8 e 0.8
- **THEN** o sistema DEVE exibir a classificação "Equilibrado" e o texto "O tamanho médio das negociações permaneceu próximo do padrão histórico do ativo, sem indícios claros de concentração ou pulverização."

#### Scenario: Classificação Fragmentado

- **WHEN** o z-score combinado está entre -1.5 e -0.8
- **THEN** o sistema DEVE exibir a classificação "Fragmentado"

#### Scenario: Classificação Muito Fragmentado

- **WHEN** o z-score combinado é menor que -1.5
- **THEN** o sistema DEVE exibir a classificação "Muito Fragmentado" e o texto "O pregão foi composto predominantemente por muitos negócios pequenos, indicando forte pulverização das negociações. Esse comportamento costuma estar associado à maior participação do varejo."

#### Scenario: Dados insuficientes para classificação

- **WHEN** há menos de 3 pregões de histórico disponíveis para o ticker
- **THEN** o sistema DEVE exibir a classificação como "—" (indisponível) e não calcular o z-score

### Requirement: Trade Density como qualificador textual

O sistema DEVE utilizar o Trade Density como informação complementar no tooltip e no texto de sumário, sem compor o score de concentração.

#### Scenario: Tooltip exibe Trade Density

- **WHEN** o usuário passa o mouse sobre o gauge ou card
- **THEN** o tooltip DEVE exibir o Trade Density do pregão mais recente e sua posição percentual no histórico

#### Scenario: Sumário textual com Trade Density

- **WHEN** o ATS está acima do P70 histórico E o Trade Density está acima do P70 histórico
- **THEN** o sumário DEVE incluir "Apesar do ticket médio elevado, o pregão apresentou alta fragmentação das negociações por faixa de preço."

#### Scenario: Sumário textual com baixa fragmentação

- **WHEN** o ATS está acima do P70 histórico E o Trade Density está abaixo do P30 histórico
- **THEN** o sumário DEVE incluir "O movimento foi sustentado por poucos negócios de grande porte, indicando maior concentração das negociações."

### Requirement: Tab renomeada e ativada

O sistema DEVE renomear a tab "Participação Institucional" para "Participação nas Negociações" e ativá-la na interface.

#### Scenario: Tab visível e clicável

- **WHEN** o usuário abre a aba "Análise do Ticker"
- **THEN** a tab "Participação nas Negociações" DEVE estar visível e clicável (state normal)

#### Scenario: Tab substitui a anterior

- **WHEN** o sistema é iniciado
- **THEN** a tab anterior "Participação Institucional" NÃO DEVE mais existir, tendo sido substituída por "Participação nas Negociações"

### Requirement: Tratamento de bordas

O sistema DEVE tratar corretamente cenários de dados ausentes ou insuficientes.

#### Scenario: Sem dados do ticker

- **WHEN** não há dados disponíveis para o ticker selecionado
- **THEN** o painel DEVE exibir o estado vazio (empty state) padrão do FlowScope

#### Scenario: Desvio padrão zero

- **WHEN** o desvio padrão histórico do ATS ou AFT é zero (todos os valores iguais)
- **THEN** o sistema DEVE usar fallback para thresholds nominais: ATS > 5000 ações = Concentrado, ATS < 500 ações = Fragmentado, senão Equilibrado

#### Scenario: Trade Density ausente

- **WHEN** o Trade Density não está disponível no all_indicators
- **THEN** o painel DEVE funcionar normalmente omitindo apenas o qualificador textual do Trade Density, sem erros ou quebras
