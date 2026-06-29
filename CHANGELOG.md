# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] — 2026-06-29

### [dominancia-pregao-stem-mfv](openspec/changes/archive/2026-06-29-dominancia-pregao-stem-mfv) Stem horizontal substitui círculo do MFV nos gráficos de Dominância; botões Mover/Ampliar da toolbar tornam-se mutuamente exclusivos

#### Changed
- **DominanceRankingChart**: círculo de MFV substituído por stem horizontal que parte de x=0 com comprimento proporcional ao MFV; label do ticker reposicionado após o stem; "Vendedores"/"Compradores" movidos para y=-0.08
- **DominanceTimelineChart**: mesma substituição círculo→stem (stem_max_data=0.15); "Vendedores"/"Compradores" movidos para y=-0.10
- **ToolbarBR**: botões Mover e Ampliar tornam-se mutuamente exclusivos (apenas um ativo por vez); Início desmarca ambos
- **OrientationPanel**: textos de orientação atualizados de "círculo" para "traço horizontal"

### [painel-dominancia-pregao](openspec/changes/archive/2026-06-29-painel-dominancia-pregao) Painéis de Dominância do Pregão (ranking) e Evolução da Dominância (timeline) com barras divergentes, classificadores e indicadores de fluxo

#### Added
- **Painel "Dominância do Pregão" na aba Análise Geral**: ranking visual de todos os tickers usando CLV do último pregão, com barras horizontais divergentes, classificação qualitativa e indicador de Money Flow Volume acumulado.
- **Painel "Evolução da Dominância" na aba Análise do Ticker**: gráfico temporal de barras divergentes (um dia por barra) com overlay de Daily Efficiency e indicador de Money Flow diário.
- **Duas novas strategies no engine**: `daily_money_flow` (MFV por dia, não acumulado) e `dominance_score` (CLV × Daily Efficiency).
- **Módulo de classificadores** (`domain/strategies/classifiers/`): `classify_dominance(clv)` e `classify_conviction(efficiency)` com tipagem forte e saída textual + score numérico.

#### Changed
- **Aba "Dominância do Pregão" renomeada para "Amplitude de Preço"** no notebook de Análise do Ticker (conteúdo atual são indicadores de amplitude).
- **Painel de orientação**: textos de ajuda para os novos painéis.
- **`_format_all_indicators`**: incluído `dominance_score` na listagem exibida.

### [multi-ticker-selector](openspec/changes/archive/2026-06-29-multi-ticker-selector) Modo visualização com Listbox de seleção múltipla, lazy refresh híbrido e remoção dos comboboxes da Análise Geral

#### Added
- **Modo visualização com Listbox(EXTENDED)**: toggle "Editar lista de tickers" alterna entre Text (edição) e Listbox (seleção múltipla via Ctrl+Click e Shift+Click)
- **Botões "Selecionar Todos" e "Desmarcar Todos"** na barra superior, ao lado direito do toggle, visíveis apenas no modo visualização
- **Preservação de seleção ao transitar entre modos**: tickers existentes mantêm marcação; novos entram marcados; remoções desaparecem; se lista mudou, recarga de dados é disparada
- **Separadores verticais** entre Salvar/Editar e entre grupo de seleção/índices
- **Lazy refresh híbrido**: aba ativa renderiza imediatamente após carga/filtro; demais abas renderizam apenas ao serem selecionadas

#### Changed
- `get_tickers()` retorna apenas tickers selecionados no modo visualização (todos no modo edição)
- `_ensure_tickers()` usa `get_all_listbox_tickers()` — carga de dados usa todos os tickers, independente da seleção
- `_on_load_data()` não substitui `self._tickers` nem chama `set_tickers()` (preserva lista original do usuário)
- Regra de quiver mantida no painel Quadrantes: setas exibidas quando apenas 1 ticker selecionado

#### Removed
- **Botão "Filtrar"** removido (seleção no Listbox já funciona como filtro)
- **Comboboxes de ticker da Análise Geral** (VWAP, Quadrantes, Dominância) removidos; seleção via Listbox controla todos os gráficos

### [refactor-analise-ticker-ui](openspec/changes/archive/2026-06-29-refactor-analise-ticker-ui) Combobox de seleção substituído por TickerList; painel Evolução da Dominância simplificado sem resumo lateral e linha de eficiência

#### Added
- **Labels "Compradores/Vendedores"** no QuadrantChart, abaixo do eixo CLV

#### Changed
- **Sub-abas reordenadas**: "Evolução da Dominância" como primeira aba da "Análise do Ticker", antes de "Amplitude de Preço"
- **DominanceTimelineChart redesenhado**: painel lateral de resumo removido; linha de eficiência (twiny) removida; informações movidas para o tooltip de cada barra (Data, Dominância, Convicção, MFV); percentuais adicionados nos labels "Compradores" e "Vendedores"
- **Spec `ticker-analysis` atualizada**: mecânica de seleção sem combobox
- **Spec `dominance-timeline-panel` atualizada**: design sem painel lateral, sem linha de eficiência, tooltip expandido

#### Removed
- **Combobox de seleção de ticker** na aba "Análise do Ticker"; ticker analisado agora deriva da TickerList (primeiro selecionado, ou primeiro da lista, ou "Selecione um ticker" se vazia)

#### Fixed
- **Hover nos charts de barra**: tooltip detecta mouse em qualquer ponto da barra (entre 0 e CLV), não apenas no endpoint
- **Zorder do tooltip**: tooltip renderiza acima dos stems MFV em ambos os charts de barra
- **Ordenação das datas**: DominanceTimelineChart ordena mais antiga no topo, mais recente na base
- **TickerList**: `exportselection=False` evita que seleção externa (X11 PRIMARY) limpe seleção interna
- **Lazy refresh**: `_on_tab_changed()` sempre atualiza a aba atual ao navegar, não apenas quando `_charts_dirty` está True

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.3.0...HEAD

[0.3.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.3.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
