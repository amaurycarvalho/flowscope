## 1. Dependências e empacotamento

- [ ] 1.1 Declarar `numpy` e `networkx` em `pyproject.toml` (dependencies) e em `requirements.txt`; verificar instalação com `pip install -e .` sem erro
- [ ] 1.2 Adicionar `networkx` aos `hiddenimports` do `flowscope.spec`; verificar que a análise do spec não levanta erro
- [ ] 1.3 Verificar que `import numpy` e `import networkx` funcionam no ambiente (`.venv`) e registrar as versões

## 2. Infraestrutura: histórico de preços em cache

- [ ] 2.1 Adicionar `CacheManager.list_dates()` (datas com arquivo diário em cache, ordenadas) e cobrir com teste em `tests/test_infrastructure`
- [ ] 2.2 Criar a porta de histórico de preços em `application/` e o leitor B3 em `infrastructure/` (lista dias úteis cacheados, usa `LastPric`); cobrir com teste de leitura somente-cache (sem rede)
- [ ] 2.3 Implementar o fallback pela `cotacao` do cache histórico de fundamentos e a seleção de **fonte única por execução**; cobrir com teste de fallback e de não-mistura
- [ ] 2.4 Reportar no resultado a fonte, o número de datas alinhadas e a janela coberta; cobrir com teste de cobertura
- [ ] 2.5 Garantir que nenhuma chamada de rede ocorre no leitor; cobrir com teste que falha se houver requisição

## 3. Domínio: análise de rede em numpy

- [ ] 3.1 Implementar alinhamento por interseção de datas, retornos e matriz de correlação; cobrir com testes de simetria, diagonal unitária e exclusão de ticker sem dados
- [ ] 3.2 Implementar Engle-Granger (OLS via `np.linalg.lstsq`) + ADF com seleção de defasagem por BIC e críticos de MacKinnon N=2; cobrir com testes de valores conhecidos (par cointegrado e par independente)
- [ ] 3.3 Implementar o gate de densidade (`MIN_OBS_CORR=30`, `MIN_OBS_COINT=60`) sinalizando indisponibilidade sem erro; cobrir com testes de cada faixa
- [ ] 3.4 Implementar half-life AR(1) do spread; cobrir com teste de par com reversão e de par sem reversão
- [ ] 3.5 Implementar o filtro de arestas (`|corr| > limiar` ou cointegrado) e a construção do grafo com comunidades, centralidade e modularidade; cobrir com testes de nós/arestas, clusters e determinismo (mesma entrada → mesmo resultado)
- [ ] 3.6 Verificar cobertura ≥ 85% do novo módulo de domínio (`pytest --cov`) e rodar o mutation testing sobre ele

## 4. Aplicação: orquestração do painel

- [ ] 4.1 Criar o caso de uso que recebe tickers e janela, chama o leitor e a análise, e devolve o resultado do painel (fonte, n, gate, grafo, clusters, modularidade); cobrir com teste de integração do fluxo

## 5. Apresentação: painel e job

- [ ] 5.1 Criar o módulo de dados do painel (montagem do dicionário de exibição, rótulos, formatação de half-life e contagens); cobrir com testes de `*_data`
- [ ] 5.2 Criar o painel em `presentation/gui/charts/` com `spring_layout(seed=42)`, cor da aresta por correlação + colorbar, estilo/espessura por cointegração + legenda, cor do nó por cluster, tamanho por centralidade, seletor de janela, estado vazio e "Copiar Gráfico"; cobrir com testes do painel
- [ ] 5.3 Implementar o job em background para carregar o histórico (padrão fila/poll) e verificar que a UI não trava; cobrir com teste do job

## 6. Integração na interface

- [ ] 6.1 Registrar a sub-aba "Rede de Correlação" em `app_tab_layout.py` (após "Dominância do Pregão") e em `_GENERAL` (`app_layout.py`); verificar com teste que a sub-aba aparece na "Análise Geral"
- [ ] 6.2 Adicionar o despacho de atualização em `_resolve_chart`/`_do_update` (`app_actions.py`); cobrir com teste de atualização ao selecionar a sub-aba
- [ ] 6.3 Adicionar o texto de orientação em `TAB_CONTENT` (`app_tabs.py`) com objetivo, pergunta, indicadores e como interpretar (incluindo a codificação visual e o gate); cobrir com teste de conteúdo
- [ ] 6.4 Garantir a restauração da última sub-aba para "Rede de Correlação" (`last_subtab`); cobrir com teste de preferências

## 7. Documentação e quality gate

- [ ] 7.1 Atualizar `panels.md` com a nova sub-aba (objetivo, pergunta, indicadores, como interpretar)
- [ ] 7.2 Rodar `ruff`, `flake8` e a suíte de testes completa; verificar zero falhas e cobertura ≥ 85%
- [ ] 7.3 Rodar o quality gate (mutation/radon/xenon conforme `Makefile`); verificar aprovação
- [ ] 7.4 Validar o build PyInstaller (`flowscope.spec`) com as novas dependências e verificar que o executável inicia
