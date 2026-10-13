## 1. Auditoria de caminhos absolutos

- [x] 1.1 Varrer os arquivos rastreados (`src/`, `tests/`, `scripts/`, `docs/`, `README.md`, `Makefile`) por padrões de caminho absoluto específico da máquina (`/home/<user>`, `/Users/`, `C:\`, drive letters) e classificar cada ocorrência entre referência a arquivo do projeto e caminho temporário/fixture/exemplo — verificação: lista de ocorrências classificadas
- [x] 1.2 Corrigir as referências a arquivos do projeto encontradas na auditoria, convertendo para caminho relativo à raiz ou derivação via `__file__`/configuração — verificação: nova varredura sem referências a arquivos do projeto e testes existentes passando

## 2. Conformidade normativa

- [x] 2.1 Confirmar que o requirement "Referências de caminho portáveis" cobre código, testes, scripts, documentação e ferramentas/agentes — verificação: `openspec validate convencao-paths-relativos` válido (warning RFC 2119 esperado e aceito)
- [x] 2.2 Revisar ocorrências de caminhos absolutos ilustrativos em specs (ex.: `/home/user/dados` em `openspec/specs/ui-polish/spec.md`) e confirmar que não são referências a arquivos do projeto — verificação: decisão registrada de que permanecem como exemplos ilustrativos

## 3. Verificação final

- [x] 3.1 Executar `make quality-gate` e confirmar lint, complexidade, duplicação, testes com cobertura e segurança — verificação: `make quality-gate` passa sem violações
