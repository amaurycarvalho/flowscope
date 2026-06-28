## Why

O painel "Quadrantes" atualmente exibe apenas um placeholder "Em desenvolvimento." — não entrega valor analítico. O gráfico de quadrantes com bolhas (CLV × VWAP Distance) preenche essa lacuna, oferecendo uma visualização compacta que responde simultaneamente a três perguntas: quem comprou/vendeu, o preço terminou acima ou abaixo do VWAP, e quanto capital sustentou esse movimento.

## What Changes

- **Novo indicador `vwap_distance`**: indicador formal derivado do VWAP, calculado como `(last_price - avg_price) / avg_price` por ticker-por-data.
- **Novo painel gráfico "Quadrantes"**: bubble chart scatter plot na sub-aba "Quadrantes" da "Análise Geral", substituindo o placeholder atual.
- **Gráfico com quiver + bolha**: dias anteriores exibidos como setas (quiver) convergindo para a bolha do dia mais recente, mostrando a trajetória temporal de cada ativo.
- **Resumo textual automático**: painel de orientação atualizado dinamicamente com análise textual da distribuição das bolhas entre os quadrantes.
- **Documentação**: `panels.md` e `indicators.md` atualizados.

## Capabilities

### New Capabilities
- `quadrant-chart`: Visualização interativa de dispersão bidimensional (CLV × VWAP Distance) com bolhas dimensionadas por `fin_instr_qty`, setas de trajetória temporal e codificação por cor divergente.
- `vwap-distance-indicator`: Indicador que mede o desvio percentual do último preço em relação ao VWAP diário, por ticker-por-data.

### Modified Capabilities
- `volume-indicators`: Adicionar requirement para o novo indicador `vwap_distance` como indicador derivado do VWAP existente.

## Impact

- **Código novo**: `src/flowscope/domain/strategies/vwap_distance.py` (estratégia do indicador), `src/flowscope/presentation/gui/charts/quadrant_chart.py` (widget matplotlib)
- **Código modificado**: `src/flowscope/domain/strategies/__init__.py` (export), `src/flowscope/domain/indicators.py` (registro), `src/flowscope/presentation/gui/app.py` (conexão do chart), `src/flowscope/application/use_cases.py` (passagem de vwap_distance no all_indicators, se necessário)
- **Documentação**: `panels.md`, `indicators.md`
- **Testes novos**: `tests/test_domain/test_vwap_distance.py`, testes para o chart (se viável com matplotlib)
- **Dependências**: nenhuma nova (matplotlib já presente)
