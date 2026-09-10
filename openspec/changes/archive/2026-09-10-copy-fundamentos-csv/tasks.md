## 1. Pré-requisito de spec

- [x] 1.1 Normalizar `openspec/specs/clipboard-export/spec.md`: trocar o cabeçalho `## ADDED Requirements` por `## Requirements` e remover o requirement duplicado "Cópia de gráfico como imagem PNG para clipboard"; verificar que `openspec validate copy-fundamentos-csv` deixa de reportar a spec como estruturalmente inválida

## 2. Montagem do CSV de Fundamentos

- [x] 2.1 Adicionar `montar_csv(dados, delimiter=";")` em `charts/fundamental_table.py` usando `_COLUNAS` (cabeçalhos) + `montar_linhas`; cobrir com teste unitário de cabeçalho, ordem das linhas, valores formatados e caso vazio
- [x] 2.2 Adicionar em `app_csv.py` um método `_build_fundamental_csv()` que filtra `_fundamental_data` por `_ticker_list.get_tickers()` (mesma regra de `_do_update`) e delega a `montar_csv`; cobrir com teste usando host fake
- [x] 2.3 Ramificar `_copy_data()` para usar `_build_fundamental_csv()` quando `_current_tabs() == ("Análise Geral", "Fundamentos")` e o CSV bruto caso contrário; cobrir com teste de cada ramo
- [x] 2.4 Tratar tabela vazia exibindo "Nenhum ticker disponível para cópia." sem copiar; cobrir com teste
- [x] 2.5 Refatorar `_copy_data()`/`_fallback_clipboard_text()` para computar o texto uma única vez e o fallback copiar o mesmo conteúdo; cobrir com teste do fallback Tkinter

## 3. Verificação

- [x] 3.1 Rodar `make test` e confirmar que os novos testes e os existentes passam (incluindo `test_fundamental_table.py`)
- [x] 3.2 Rodar `make lint` e corrigir eventuais achados do `ruff`

## 4. Validação final

- [x] 4.1 Validar a change com `openspec validate copy-fundamentos-csv --strict` e resolver avisos aplicáveis
