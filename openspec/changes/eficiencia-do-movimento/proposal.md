## Why

A sub-aba "Eficiência do Movimento" existe como placeholder desabilitado, exibindo apenas valores brutos de `daily_efficiency` em um Text widget. O indicador já está implementado e disponível nos dados, mas o painel atual não oferece visualização ou interpretação — não responde a uma pergunta clara sobre o comportamento do mercado. A reformulação transforma esse espaço morto em um painel analítico que responde a uma pergunta fundamental e distinta dos demais painéis.

## What Changes

- Substituir o placeholder Text desabilitado por um `EfficiencyPanel` com três componentes visuais empilhados (card, gauge horizontal, histórico de barras)
- Criar `classify_efficiency()` em `domain/strategies/classifiers/` com 5 níveis de classificação (Muito Baixa a Muito Alta)
- O painel responde à pergunta: **"O pregão gerou progresso ou apenas ruído?"**
- **Card superior**: classificação qualitativa, valor percentual da eficiência, texto automático explicativo
- **Gauge horizontal**: escala 0–1 com faixas coloridas (Ruído/Intermediário/Progresso) e marcador da eficiência atual
- **Histórico**: barras horizontais coloridas por faixa de eficiência para os últimos 15 pregões, com tooltip em todas as barras mostrando eficiência, range, range%, CLV, fechamento e preço médio
- Renomear a label exibida ao usuário de "Daily Efficiency" para "Eficiência do Movimento" (manter `daily_efficiency` como identificador interno)
- Habilitar a sub-aba no notebook de ticker

## Capabilities

### New Capabilities
- `movement-efficiency-panel`: Painel visual de Eficiência do Movimento com classificação qualitativa, gauge horizontal e histórico de barras para o ticker selecionado

### Modified Capabilities
- *(nenhuma — capability nova, sem alteração de requisitos em specs existentes)*

## Impact

- **Novo arquivo**: `src/flowscope/presentation/gui/charts/efficiency_panel.py` (~300 linhas)
- **Modificado**: `src/flowscope/presentation/gui/app.py` — registrar e habilitar o novo painel, atualizar orientação
- **Modificado**: `src/flowscope/domain/strategies/classifiers/__init__.py` — exportar novo classificador
- **Novo arquivo**: `src/flowscope/domain/strategies/classifiers/efficiency.py` — classificador de eficiência
- **Modificado**: `panels.md` — documentar novo layout e pergunta
- Nenhuma mudança em infraestrutura, banco de dados ou dependências externas
