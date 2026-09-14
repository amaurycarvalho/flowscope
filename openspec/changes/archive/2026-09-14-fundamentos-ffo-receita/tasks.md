## 1. Provider Fundamentus (Receita e Rend. Distribuído)

- [x] 1.1 Adicionar as constantes `CAMPO_RECEITA_12M`, `CAMPO_RECEITA_3M`, `CAMPO_RENDIMENTOS_12M` e `CAMPO_RENDIMENTOS_3M` e incluí-las em `CAMPOS_FUNDAMENTAIS` em `src/flowscope/application/fundamental_ports.py`; verificar que cada constante está no frozenset.
- [x] 1.2 Mapear `Receita` (com fallback para `Receita Líquida`) e `Rend. Distribuído` de `demonstrativos_12m/3m` em `campos_do_ativo` no adapter; verificar que `campos_do_ativo` de uma fixture de FII expõe os quatro campos.
- [x] 1.3 Cobrir no teste do provider/adapter os cenários de `Receita`, `Receita Líquida` como alternativa e campo ausente; rodar `.venv/bin/python -m pytest tests/test_infrastructure/test_fundamentus_provider.py`.

## 2. Domínio (razões e tendência)

- [x] 2.1 Criar `MotivoMargem` (`RECEITA_NEGATIVA`, `FFO_NEGATIVO`, `RECEITA_E_FFO_NEGATIVOS`) e `ResultadoMargem` (`valor`, `motivo`) em `src/flowscope/domain/fii/metrics.py`.
- [x] 2.2 Implementar as funções puras `ffo_receita`, `dividendos_receita` e `dividendos_ffo`, com as regras de insumo negativo e divisão por zero da spec.
- [x] 2.3 Implementar `tendencia_margem_ffo(margem_12m, margem_3m)` como `classificar_tendencia_ffo(margem_3m - margem_12m)`, retornando `None` quando faltar margem.
- [x] 2.4 Exportar os novos símbolos em `src/flowscope/domain/fii/__init__.py` quando aplicável; verificar que os imports do pacote funcionam.
- [x] 2.5 Testes unitários cobrindo os exemplos BTLG11/CACR11, os três textos de negativo e divisão por zero; rodar `.venv/bin/python -m pytest tests/test_domain`.

## 3. Aplicação (montagem e recálculo do DY)

- [x] 3.1 Adicionar o value object `MargensFii` e o campo `margens: MargensFii | None` em `AnaliseFundamental` (`src/flowscope/domain/fii/analysis.py`).
- [x] 3.2 Em `_analisar_ticker`, montar `MargensFii` apenas quando `exibicao.tipo == TIPO_EXIBICAO_FII`, a partir dos campos de Receita, FFO e Rend. Distribuído; verificar com teste de caso de uso que Tipo `Papel` resulta em `margens=None`.
- [x] 3.3 Recalcular o Dividend Yield de FII como `(ultimo_dividendo.valor * 12) / cotacao` via `dataclasses.replace`, mantendo o valor do Fundamentus quando o insumo faltar; teste de caso de uso com e sem insumos.
- [x] 3.4 Rodar `.venv/bin/python -m pytest tests/test_application`.

## 4. Apresentação (colunas, formatação e orientação)

- [x] 4.1 Atualizar `_COLUNAS` e `_COLUNAS_DIREITA` em `src/flowscope/presentation/gui/charts/fundamental_rows.py`: remover `ffo_yield`, `dividend_payout` e `p_ffo`; inserir as seis razões; posicionar `ffo_trend` após `ffo_receita_3m`; total de 29 colunas.
- [x] 4.2 Adicionar em `fundamental_formatters.py` a tradução de `ResultadoMargem` para célula (`motivo` -> texto; `valor` -> `formatar_percentual(valor, 1)`; ausente -> `N/A`).
- [x] 4.3 Atualizar `_linha_analise` para emitir as novas colunas na ordem definida, exibindo `N/A` para Tipo `Papel` e para dado ausente.
- [x] 4.4 Atualizar o texto de orientação da sub-aba em `src/flowscope/presentation/gui/app_tabs.py` e o espelho em `panels.md`, incluindo a leitura de `Dividendos/FFO` (100%).
- [x] 4.5 Atualizar `tests/test_presentation/test_fundamental_table.py` (cabeçalho CSV com 29 colunas, índices das novas colunas e `TAB_CONTENT`); rodar `.venv/bin/python -m pytest tests/test_presentation`.

## 5. Verificação final

- [x] 5.1 Rodar `make lint` e corrigir todos os apontamentos de ruff/flake8.
- [x] 5.2 Rodar `make test` e garantir cobertura >= 85% sem falhas.
- [x] 5.3 Conferir o comportamento observável: o CSV da tabela tem o cabeçalho com as 29 colunas na ordem da spec e os exemplos BTLG11/CACR11 produzem `87,3%`/`85,5%`, `104,0%` -> `Receita e FFO negativos` e as tendências `Estável`/`N/A`.
