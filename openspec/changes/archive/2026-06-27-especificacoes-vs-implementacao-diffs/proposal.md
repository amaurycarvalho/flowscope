## Why

Auditoria comparativa entre as especificações e a implementação real revelou divergências que precisam ser documentadas para alinhar specs com o código.

## What Changes

- `data-ingestion`: B3 API descrita como POST mas implementada como GET — spec desatualizada
- `data-ingestion`: Exemplo de datas Fibonacci no spec diverge do cálculo real implementado
- `clipboard-export`: Cópia CSV tem fallback Tkinter não descrito no spec; falha de cópia de imagem usa `print(stderr)` em vez de feedback na GUI
- `project-scaffold`: `requirements.txt` não inclui `requests>=2.28` presente no `pyproject.toml`; README tem seção "Interface desktop" vazia
- `volume-indicators`: Sem teste para cenário "Menos de 15 tickers disponíveis"
- `desktop-shortcut`: Sem teste para cenários Windows/macOS

## Capabilities

### Modified Capabilities

- `data-ingestion`: fluxo two-step da API B3 (POST → GET), exemplo de datas Fibonacci
- `clipboard-export`: fallback Tkinter na cópia CSV e comportamento de erro na cópia de imagem

## Impact

- `openspec/specs/data-ingestion/spec.md` — corrigir descrição do fluxo HTTP e exemplo de datas
- `openspec/specs/clipboard-export/spec.md` — adicionar fallback Tkinter, corrigir cenário de falha
- `requirements.txt` — adicionar `requests>=2.28`
- `README.md` — preencher ou remover seção vazia "Interface desktop"
- `tests/` — adicionar testes faltantes para volume-indicators e desktop-shortcut (se desejado)
