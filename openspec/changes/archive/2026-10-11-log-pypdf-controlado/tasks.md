## 1. Caminho de log em módulo neutro

- [x] 1.1 Mover `presentation/log_paths.py` para `flowscope/log_paths.py` e atualizar os imports em `presentation/main.py` e `presentation/gui/app_about_actions.py` (mantendo o nome `log_file_path` importado); verificar `tests/test_presentation/test_version_check.py` e `tests/architecture/test_layer_boundaries.py` verdes.

## 2. Controle do log do `pypdf` no processo principal

- [x] 2.1 Adicionar um helper idempotente que silencia o logger `pypdf` para `ERROR` (suprime `WARNING`/`INFO`/`DEBUG`) e chamá-lo em `_configure_logging`; verificar com teste unitário que o nível de `logging.getLogger("pypdf")` fica `ERROR` e que `_configure_logging` invoca o helper (monkeypatch), restaurando o nível após o teste.

## 3. Controle do log do `pypdf` no worker de extração

- [x] 3.1 Em `application/extracao_orcada.py`, configurar de forma idempotente o logger `pypdf` no processo filho (`_extrair_pdf_filho`): nível `ERROR` e um `FileHandler` no arquivo de log do app (mesmo formato do app, `propagate=False`); verificar com teste unitário que um `WARNING` do `pypdf` é descartado e um `ERROR` é gravado no arquivo (usando `tmp_path`, sem PDF real).

## 4. Verificação integrada

- [x] 4.1 Rodar `pytest` (marker padrão) e confirmar a suíte verde, e rodar `openspec validate log-pypdf-controlado --strict`.
- [x] 4.2 Conferir manualmente (observação, sem o PDF problemático versionado) que a extração do PDF do AGRO3 com `xref` inválido não escreve mais avisos do `pypdf` no terminal e que eventuais `ERROR` do `pypdf` aparecem no arquivo `flowscope.log`.
