## Why

O painel "Participação Institucional" existe no FlowScope mas está desabilitado. Seu nome e conceito original afirmavam identificar a presença de investidores institucionais nos dados públicos da B3 — uma afirmação que os dados consolidados não suportam diretamente, pois a B3 não divulga a identidade dos participantes. Isso cria um risco de interpretação enganosa. O painel precisa ser reformulado para medir o que os dados realmente permitem: o grau de concentração das negociações, permitindo inferir (sem afirmar) o perfil provável da participação.

## What Changes

- Renomear a tab "Participação Institucional" para "Participação nas Negociações" na GUI
- Criar um novo painel visual (chart panel) com três componentes:
  - **Gauge horizontal** — Índice de Concentração das Negociações (score combinado de ATS + AFT normalizados por percentis históricos do próprio ativo)
  - **Card informativo** — Average Financial Ticket (R$) e Average Trade Size (ações/negócio), com variação percentual vs. mediana histórica
  - **Timeline** — Evolução do Average Financial Ticket nos últimos 30 pregões, com linha horizontal da mediana do período
- Implementar classificação qualitativa baseada em z-score do histórico do próprio ativo:
  - Muito Fragmentado, Fragmentado, Equilibrado, Concentrado, Muito Concentrado
- Ativar a tab "Participação nas Negociações" na interface
- Trade Density usado apenas como qualificador textual em tooltips, não compondo o score

## Capabilities

### New Capabilities
- `participation-negociacoes`: Painel visual que mostra o grau de concentração das negociações de um ativo, com gauge de concentração, cards informativos e evolução temporal do ticket médio financeiro

### Modified Capabilities
*(nenhuma — capability nova)*

## Impact

- **GUI**: `src/flowscope/presentation/gui/app.py` — renomear tab, adicionar novo panel, ativar tab
- **Novo panel**: `src/flowscope/presentation/gui/charts/participation_panel.py` — novo chart panel
- **Nova estratégia** (opcional): se necessário criar indicador de Índice de Concentração em `src/flowscope/domain/strategies/`
- **Infraestrutura**: o painel precisará de acesso ao histórico completo de indicadores (não só o pregão atual) para calcular percentis/z-score — pode exigir modificação em como os dados são passados aos panels
- **Nenhuma dependência nova** — utiliza matplotlib (já existente) e os indicadores `average_trade_size`, `average_financial_ticket` e `trade_density` já implementados
