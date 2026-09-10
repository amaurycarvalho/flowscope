## Context

Ver `proposal.md - Why`. Estado atual relevante:

- `CsvMixin` (`app_csv.py`) concentra a cópia: `_copy_data()` monta o CSV bruto via `_build_raw_csv()` e copia com `pyxclip`, caindo em `_fallback_clipboard_text()` (que remonta o CSV e usa o clipboard do Tkinter).
- A tabela de Fundamentos é renderizada por `FundamentalTablePanel` (`charts/fundamental_table.py`) a partir de `montar_linhas(dados)`, com cabeçalhos definidos em `_COLUNAS`.
- `_do_update` (`app_actions.py`) alimenta o painel com `{t: dados[t] for t in tickers if t in dados}`, onde `tickers = self._ticker_list.get_tickers()`; `_fundamental_data` guarda os resultados por ticker.
- `TabActionsMixin._current_tabs()` já resolve `(aba_principal, sub_aba)`.
- **Problema pré-existente**: `openspec/specs/clipboard-export/spec.md` é estruturalmente inválido (começa com `## ADDED Requirements` em vez de `## Requirements` e contém um requirement duplicado de "Cópia de gráfico como imagem PNG"). O archive recusa deltas para essa capability até a spec ser normalizada.

## Goals / Non-Goals

**Goals:**

- Copiar, na sub-aba Fundamentos, exatamente as linhas exibidas na tabela, com cabeçalho e ordem preservados.
- Reutilizar o mecanismo de clipboard e o feedback existentes, sem novos caminhos de cópia.
- Manter o comportamento atual em todas as demais abas/sub-abas.

**Non-Goals:**

- Alterar o formato do CSV bruto de negociações.
- Exportar Fundamentos para arquivo ou adicionar novos botões/atalhos.
- Copiar valores "crus" (não formatados) da tabela.

## Decisions

### 1. Detecção do contexto pela combinação de abas

Reutilizar `TabActionsMixin._current_tabs()`; o ramo de Fundamentos vale quando `(main_tab, sub_tab) == ("Análise Geral", "Fundamentos")`.

**Alternativas:** inspecionar `_general_notebook` diretamente em `app_csv.py` (duplica lógica já existente) → rejeitada.

### 2. Montar o CSV a partir das mesmas linhas da tabela

Expor uma função pura `montar_csv(dados, delimiter=";")` em `fundamental_table.py` que usa `_COLUNAS` (cabeçalhos) + `montar_linhas(dados)`. A tabela e a cópia passam a compartilhar a mesma fonte de verdade.

**Alternativas:** ler `Treeview.get_children()`/`item(..., "values")` do painel (fiel ao exibido, porém acopla o `CsvMixin` aos detalhes internos do painel e exige display para testar) → rejeitada.

### 3. Escopo de linhas igual ao da tabela

Filtrar `_fundamental_data` por `self._ticker_list.get_tickers()` da mesma forma que `_do_update`, garantindo que o CSV reflita os tickers exibidos.

### 4. Formato: `;` com valores formatados

Usar separador `;` e os valores já formatados como na tabela (ex.: `8,16%`, `12,25x`, `N/A`), consistente com o padrão brasileiro da capability `clipboard-export`.

**Alternativas:** exportar valores numéricos crus (inconsistente com a tabela e com o CSV existente) → rejeitada.

### 5. Computar o texto uma única vez

Refatorar `_copy_data()` para montar o texto do ramo correto e passá-lo a `_fallback_clipboard_text(csv_text)`, evitando recomputar e garantindo que o fallback copie o mesmo conteúdo.

### 6. Tabela vazia

Reutilizar a mensagem existente "Nenhum ticker disponível para cópia." e não copiar nada quando não houver linhas.

## Risks / Trade-offs

- **[Risco] `clipboard-export` principal estruturalmente inválido bloqueia o archive** → normalizar a spec principal (`## ADDED Requirements` → `## Requirements`; remover o requirement PNG duplicado) antes de arquivar esta change; registrar como tarefa.
- **[Risco] Usuário esperar valores numéricos crus em vez de formatados** → decisão registrada (formato exibido); revisável antes da implementação.
- **[Risco] `_fundamental_data` vazio se a análise ainda não rodou** → coberto pelo cenário de tabela vazia.

## Migration Plan

1. Normalizar `openspec/specs/clipboard-export/spec.md` (seção `## Requirements`, remover duplicata) para permitir o archive.
2. Implementar o ramo de cópia e a função `montar_csv`; cobrir com testes unitários da função pura e do ramo de cópia.
3. **Rollback:** remover o ramo de Fundamentos de `_copy_data`, voltando ao CSV bruto; a função `montar_csv` pode permanecer sem uso.
