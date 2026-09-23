## 1. Série do campo Shorts%

- [x] 1.1 Em `src/flowscope/presentation/gui/charts/fundamental_evolution_data.py`, adicionar a constante `TIPO_PERCENTUAL_1` e o extrator `_shorts_pct` (retornando `analise.short.shorts_pct if analise.short else None`) e incluir `CampoEvolucao("shorts_pct", "Shorts%", TIPO_PERCENTUAL_1, _shorts_pct)` ao fim de `CAMPOS_EVOLUCAO`; verificar que `montar_series` passa a devolver oito séries com `shorts_pct` presente
- [x] 1.2 Em `fundamental_evolution_panel.py`, mapear `TIPO_PERCENTUAL_1` em `_FORMATADORES` para `formatar_percentual(valor, 1)`; verificar com `formatar_ponto(TIPO_PERCENTUAL_1, Decimal("0.1")) == "10,0%"`
- [x] 1.3 Atualizar `tests/test_presentation/test_fundamental_evolution_data.py` (contagem 7→8, tipo de `shorts_pct` e extração de `MetricasShort`) e rodar `python -m pytest tests/test_presentation/test_fundamental_evolution_data.py -q`

## 2. Painel: grade, data e tooltip

- [x] 2.1 Em `fundamental_evolution_panel.py`, usar os oito eixos da grade (trocar `range(self._LINHAS * self._COLUNAS - 1)` por `range(self._LINHAS * self._COLUNAS)`); verificar que os oito títulos são definidos, incluindo `Shorts%`
- [x] 2.2 Trocar o rótulo de data de `strftime("%m/%y")` para `strftime("%d/%m/%y")` e reutilizar o mesmo formato no texto do tooltip; verificar que o eixo exibe `DD/MM/AA` (ex.: `01/09/26`)
- [x] 2.3 Implementar o tooltip de hover: conectar `motion_notify_event`, manter uma anotação por eixo (recriada ao desenhar a série), escolher o ponto mais próximo em pixels com um limiar e exibir data e valor formatado; verificar com evento de mouse simulado que a anotação aparece com o ponto e some fora do limiar
- [x] 2.4 Limpar/ocultar as anotações em `update`, `reset` e no estado vazio; verificar que nenhuma anotação persiste entre redesenhos no teste do painel
- [x] 2.5 Atualizar `tests/test_presentation/test_fundamental_evolution_panel.py` (oito painéis, formato de data e tooltip) e rodar `python -m pytest tests/test_presentation/test_fundamental_evolution_panel.py -q`

## 3. Orientação e documentação

- [x] 3.1 Em `src/flowscope/presentation/gui/app_tabs.py`, incluir `shorts_pct` em `TAB_CONFIGS` e atualizar `TAB_CONTENT` da sub-aba ("oito mini-gráficos" e `Shorts%` em indicadores/como interpretar); verificar que o texto da sub-aba cita os oito campos
- [x] 3.2 Em `panels.md`, atualizar a lista de campos, o diagrama da grade 4x2 (ocupando a oitava célula) e a seção de interação (tooltip); verificar que `panels.md` não menciona mais "sete mini-gráficos"
- [x] 3.3 Atualizar `tests/test_presentation/test_fundamental_evolution_integration.py` para o novo texto do OrientationPanel e rodar `python -m pytest tests/test_presentation/test_fundamental_evolution_integration.py -q`

## 4. Verificação final

- [x] 4.1 Rodar `make lint complexity` e garantir que `ruff`/`flake8` passam sem novas violações
- [x] 4.2 Rodar `make test` (cobertura ≥ 85%) e garantir que toda a suíte passa
- [x] 4.3 Revisar os testes novos quanto à cobertura de mutação dos ramos adicionados (extração ausente, formatação com uma casa, limiar do tooltip)
