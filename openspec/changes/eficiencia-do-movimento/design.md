## Context

A sub-aba "Eficiência do Movimento" em `src/flowscope/presentation/gui/app.py:246` é um placeholder desabilitado com um widget `Text` exibindo valores brutos. O indicador `daily_efficiency` já é calculado por `DailyEfficiencyStrategy` em `src/flowscope/domain/strategies/efficiency.py` e está disponível via `all_indicators["daily_efficiency"]` como `dict[date, Decimal]` por ticker.

O painel `PriceRangePanel` (Amplitude de Preço) já consome `daily_efficiency` como barra de fundo, mas sem interpretação dedicada — a eficiência é secundária naquele contexto. Este design cria um painel independente que torna a eficiência o foco principal.

## Goals / Non-Goals

**Goals:**
- Criar `EfficiencyPanel` visual com três componentes: card de classificação, gauge horizontal e histórico de barras
- Implementar `classify_efficiency()` com 5 níveis qualitativos com base em thresholds fixos de eficiência
- Habilitar tooltip hover em todas as barras do histórico (não apenas no dia atual)
- Habilitar a sub-aba no notebook de ticker
- Reaproveitar o padrão arquitetural de `FinancialFlowPanel` (GridSpec, card sem eixos, toolbar, empty state)

**Non-Goals:**
- Não alterar o cálculo de `daily_efficiency` (fórmula já estabelecida)
- Não criar novas estratégias de indicador no domínio
- Não modificar o pipeline de dados ou use cases existentes
- Não adicionar dependências externas

## Decisions

### 1. Thresholds fixos (não adaptativos) para classificação
A classificação usa faixas fixas: 0–0.20 (Muito Baixa), 0.20–0.40 (Baixa), 0.40–0.60 (Moderada), 0.60–0.80 (Alta), >0.80 (Muito Alta). Diferente do Range% na Amplitude de Preço (que usa mediana histórica), a eficiência tem significado absoluto: 0 = ruído puro, 1 = convicção pura. Thresholds adaptativos adicionariam complexidade sem ganho interpretativo.

### 2. Tooltip em todas as barras do histórico
Seguindo o padrão do `PriceRangePanel._on_motion`, o hover detecta a barra mais próxima no eixo Y e exibe tooltip com dados completos (eficiência, range, range%, CLV, fechamento, preço médio). Isso é mais informativo que o tooltip apenas no dia atual (como faz o `FinancialFlowPanel`).

### 3. Gauge horizontal como subplot separado, não integrado ao card
O gauge tem escala própria (0 a 1), eixos e labels que não se misturam bem com o card sem eixos. Separar em dois subplots (`height_ratios=[2, 1, 3]`) mantém cada componente limpo e facilita manutenção.

### 4. 15 pregões no histórico
Mesmo período do `PriceRangePanel` para consistência visual entre abas. Barra atual destacada com opacidade/linha mais escura.

### 5. Cores das faixas do gauge
- 0.00–0.30: vermelho (#CC4444) — "Ruído"
- 0.30–0.60: amarelo (#CCAA44) — "Intermediário"
- 0.60–1.00: verde (#44AA66) — "Progresso"

Mesma paleta já usada no `PriceRangePanel` para as barras de fundo de eficiência, garantindo consistência visual.

### 6. Nomenclatura
- Interno: `daily_efficiency` (indicador), `EfficiencyPanel` (classe), `classify_efficiency` (classificador)
- Exibido ao usuário: "Eficiência do Movimento"

## Risks / Trade-offs

- **Sobreposição com Amplitude de Preço**: Ambos os painéis falam de eficiência. A Amplitude usa eficiência como contexto (barra de fundo); a Eficiência a torna o foco principal. Risco baixo de confusão — as perguntas são diferentes.
- **Thresholds fixos podem não capturar ativos extremos**: Um ativo muito volátil pode raramente atingir "Muito Alta". Isso é aceitável — a classificação reflete mérito absoluto, não relativo. Se o ativo nunca atinge alta eficiência, isso é um achado legítimo sobre seu comportamento.
- **Tooltip no hover pode sobrepor marcadores**: O `PriceRangePanel` já lida com isso posicionando o tooltip relativo ao cursor. O mesmo padrão será usado.
