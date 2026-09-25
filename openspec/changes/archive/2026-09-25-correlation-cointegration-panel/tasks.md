## 1. Dependências e empacotamento

- [x] 1.1 Declarar `numpy` e `networkx` (`networkx>=3,<4`) em `pyproject.toml` (dependencies) e em `requirements.txt`; verificar instalação com `pip install -e .` sem erro
- [x] 1.2 Adicionar `numpy` e `networkx` aos `hiddenimports` do `flowscope.spec`; verificar que a análise do spec não levanta erro
- [x] 1.3 Verificar que `import numpy` e `import networkx` funcionam no ambiente (`.venv`) e registrar as versões

## 2. Mapeamento dos dados carregados

- [x] 2.1 Criar o módulo de dados do painel (`presentation/gui/charts/network_data.py`): a partir de `_current_data` e da seleção do Listbox, extrair `dict[ticker, list[(data, last_price)]]` e montar os rótulos/formatações do painel; cobrir com testes de `*_data`
- [x] 2.2 Garantir que o mapeamento descarta preços ausentes/não positivos e informa tickers sem dados; cobrir com teste

## 3. Domínio: análise de rede em numpy

- [x] 3.1 Implementar alinhamento por interseção de datas, retornos entre observações consecutivas e a matriz de correlação **assinada**; cobrir com testes de simetria, diagonal unitária, sinal e exclusão de ticker sem dados
- [x] 3.2 Implementar o diagnóstico de amostragem (n de observações, span e gaps mín/mediana/máx em dias úteis); cobrir com teste
- [x] 3.3 Implementar Engle-Granger (OLS via `np.linalg.lstsq`) + ADF em `numpy`, com seleção de defasagem por BIC, críticos de MacKinnon (2 variáveis) e direção determinística; cobrir com testes de valores conhecidos (par cointegrado e par independente)
- [x] 3.4 Implementar o gate de densidade (`MIN_OBS_CORR=30`, `MIN_OBS_COINT=40`) sinalizando indisponibilidade sem erro; cobrir com testes de cada faixa
- [x] 3.5 Implementar half-life AR(1) do spread em número de observações (e aproximação em dias); cobrir com teste de par com reversão e de par sem reversão
- [x] 3.6 Implementar o filtro de arestas (`|corr| > limiar` ou cointegrado) e a construção do grafo com comunidades, centralidade e modularidade; cobrir com testes de nós/arestas, clusters e determinismo (mesma entrada → mesmo resultado)
- [x] 3.7 Verificar cobertura ≥ 85% do novo módulo de domínio (`pytest --cov`)

## 4. Apresentação: painel

- [x] 4.1 Criar o painel em `presentation/gui/charts/` com `spring_layout(seed=42)`, cor da aresta por correlação assinada (escala −1..+1) + colorbar, estilo/espessura por cointegração + legenda, cor do nó por comunidade, tamanho por centralidade, diagnóstico de amostragem, estados vazios/avisos e "Copiar Gráfico"; cobrir com testes do painel
- [x] 4.2 Garantir que o painel **não** possui seletor de janela próprio e que o cálculo roda sobre os dados já carregados; cobrir com teste
- [x] 4.3 Ajustar a mensagem de estado vazio por observações insuficientes para quebra de linha automática (`wrap=True`), cabendo na largura da figura; cobrir com teste de `wrap` e de largura renderizada ≤ figura
- [x] 4.4 Reutilizar a mesma `ToolbarBR` do VWAP (Início, Voltar, Avançar, Mover, Ampliar, Salvar, "Copiar Gráfico") no painel da rede; cobrir com teste de paridade de `toolitems`/botões e de navegação
- [x] 4.5 Corrigir a ordem de empacotamento (toolbar antes do canvas) para a toolbar não ser espremida em janelas baixas pela figura retrato; cobrir com teste de visibilidade em janela baixa

## 5. Integração na interface

- [x] 5.1 Registrar a sub-aba "Rede de Correlação" em `app_tab_layout.py` (após "Dominância do Pregão") e em `_GENERAL` (`app_layout.py`); verificar com teste que a sub-aba aparece na "Análise Geral"
- [x] 5.2 Adicionar o tratamento da rede em `_resolve_chart`/`_do_update` (`app_actions.py`); cobrir com teste de atualização ao selecionar a sub-aba e de recálculo ao mudar período/amostragem
- [x] 5.3 Adicionar o texto de orientação em `TAB_CONTENT` (`app_tabs.py`) com objetivo, pergunta, indicadores e como interpretar (codificação visual, gates, limitações da amostragem e orientação para usar "Todos os dias"); cobrir com teste de conteúdo
- [x] 5.4 Garantir a restauração da última sub-aba para "Rede de Correlação" (`last_subtab`); cobrir com teste de preferências

## 6. Documentação e quality gate

- [x] 6.1 Atualizar `panels.md` com a nova sub-aba (objetivo, pergunta, indicadores, como interpretar, uso dos combos globais e limitações da amostragem).
- [x] 6.2 Avaliar se precisa atualizar `README.md` e `indicators.md`, procedendo a atualização se necessário.
- [x] 6.3 Rodar `make lint` e `make complexity`, corrigindo pendências
- [x] 6.4 Rodar `make test`, corrigindo pendências
- [x] 6.5 Validar o build PyInstaller (`flowscope.spec`) com as novas dependências e verificar que o executável inicia
