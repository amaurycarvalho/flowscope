## 1. Corrigir data-ingestion/spec.md

- [x] 1.1 Alterar descrição do fluxo two-step de POST para GET com query params (`/api/download/requestname?fileName=...&date=...`)
- [x] 1.2 Corrigir exemplo de datas Fibonacci: ref_date 2026-06-26 → 2026-06-25, 2026-06-24, 2026-06-23, 2026-06-22, 2026-06-18, 2026-06-15, 2026-06-05

## 2. Corrigir clipboard-export/spec.md

- [x] 2.1 Adicionar cenário de fallback Tkinter na cópia CSV (quando pyxclip não está disponível)
- [x] 2.2 Corrigir cenário de falha na cópia de imagem: `print(stderr)` substituído por `ClipboardError` com feedback na barra de status da GUI

## 3. Corrigir project-scaffold

- [x] 3.1 Adicionar `requests>=2.28` no `requirements.txt`
- [x] 3.2 Remover seção vazia "Interface desktop" no `README.md`

## 4. Registrar testes faltantes

- [x] 4.1 Teste existente (`test_all_when_less_than_n` em `test_indicators.py`) já cobre o cenário "< 15 tickers"
- [x] 4.2 Adicionar `tests/test_presentation/test_main.py` com testes para desktop-shortcut em Windows e macOS
