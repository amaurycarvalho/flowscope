## 1. OrientationPanel — tags e novo set_content

- [x] 1.1 Adicionar `tag_config("bold")` e `tag_config("italic")` no `__init__` do OrientationPanel
- [x] 1.2 Refatorar `set_content` para aceitar `body: list[tuple[str, str]]` e aplicar tags ao inserir texto

## 2. Refatorar _tab_content em app.py — Análise Geral

- [x] 2.1 Converter body da VWAP para lista de tuplas com tags bold/italic
- [x] 2.2 Converter body dos Quadrantes para lista de tuplas
- [x] 2.3 Converter body da Dominância do Pregão para lista de tuplas

## 3. Refatorar _tab_content em app.py — Análise do Ticker

- [x] 3.1 Converter body da Evolução da Dominância para lista de tuplas
- [x] 3.2 Converter body da Amplitude de Preço para lista de tuplas
- [x] 3.3 Converter body do Fluxo Financeiro para lista de tuplas
- [x] 3.4 Converter body da Participação Institucional para lista de tuplas
- [x] 3.5 Converter body da Eficiência do Movimento para lista de tuplas
- [x] 3.6 Converter body do Resumo Geral para lista de tuplas

## 4. Atualizar _on_quadrant_summary

- [x] 4.1 Atualizar `_on_quadrant_summary` para anexar summary como tupla ao final da lista body, em vez de concatenação de string

## 5. Verificação

- [x] 5.1 Navegar por todas as sub-abas e confirmar que cabeçalhos estão em negrito e perguntas em itálico
