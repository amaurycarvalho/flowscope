# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] — 2026-07-01

### [orientation-add-question-field](openspec/changes/archive/2026-07-01-orientation-add-question-field) Pergunta-guia adicionada ao conteúdo de orientação de cada sub-aba

#### Changed
- Conteúdo do OrientationPanel passa a incluir "Responde a pergunta" entre Objetivo e Indicadores envolvidos
- Ordem dos campos: **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**

### [orientation-richtext-formatting](openspec/changes/archive/2026-07-01-orientation-richtext-formatting) Formatação rica nativa (negrito/itálico) no OrientationPanel via tags tk.Text

#### Added
- Formatação rica: cabeçalhos de seção em **negrito** e perguntas em itálico via tags nativas `tk.Text`
- Configuração das tags `"bold"` (TkDefaultFont 9 bold) e `"italic"` (TkDefaultFont 9 italic)

#### Changed
- `set_content` alterado de `(title: str, body: str)` para `(title: str, body: list[tuple[str, str]])`
- Todas as 9 sub-abas refatoradas para usar lista de tuplas `(segmento, tag)`
- `_on_quadrant_summary` atualizado para anexar resumo como tupla à lista body

### [unify-price-amplitude-chart](openspec/changes/archive/2026-07-01-unify-price-amplitude-chart) Três métricas correlatas unificadas num único axes com camadas visuais de posição, amplitude e eficiência

#### Changed
- Price Range Timeline, Range % Histórico e Eficiência Diária unificados num único axes matplotlib com 3 camadas visuais por row (eficiência como barra de fundo, timeline como scatter, amplitude como tamanho do marcador)
- Tooltip expandida com Amplitude Relativa (Range %)
- Nomenclatura atualizada: título "Amplitude de Preço — {ticker}", "Range %" → "Amplitude Relativa"
- Texto de orientação atualizado com as três perguntas "Onde / Quanto / Se andou com convicção" e significado interpretativo das classificações
- Setas de trajetória (ax.arrow) substituídas por linhas (ax.plot) — eliminou artefatos visuais de traçado extra
- Labels "← Vendedores" e "Compradores →" adicionados abaixo do gauge CLV
- Título do CLV alterado para "CLV (data mais recente)"
- Labels "Min:" e "Max:" separados e posicionados abaixo de 0% e 100%
- Altura do gauge CLV reduzida em ~20%

#### Removed
- Sub-gráfico "Range % Histórico" — substituído pelo tamanho do marcador de fechamento (●)
- Sub-gráfico "Eficiência Diária" — substituído por barra horizontal de fundo por row (eficiência visível em todos os dias, não apenas no último)

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v0.4.0...HEAD

[0.4.0]: https://github.com/amaurycarvalho/flowscope/releases/tag/v0.4.0
See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
