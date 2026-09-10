## 1. Domínio do FFO

- [x] 1.1 Criar `FFOComponentType` e `FFOComponent` (valor, tipo, proveniência) em `domain/ffo/` e verificar com teste unitário
- [x] 1.2 Implementar a tabela de regras versionada de classificação e verificar com testes de componentes recorrentes, fair value, alienação, não recorrentes e `UNKNOWN`
- [x] 1.3 Implementar `calculate_ffo` (soma apenas dos recorrentes) e verificar com o exemplo da RFC-010 (`FFO = 8.000.000`)
- [x] 1.4 Implementar FFO mensal/12m com validação de competência e verificar com teste de janela completa e de base insuficiente
- [x] 1.5 Implementar FFO por cota com média ponderada de cotas e verificar com teste de ponderação por tempo
- [x] 1.6 Implementar FFO Yield e P/FFO com preço da data (ou último pregão anterior, registrando `market_price_date`) e verificar a relação `P/FFO = 1 / FFO Yield`
- [x] 1.7 Implementar qualidade (`HIGH`/`MEDIUM`/`LOW`) por materialidade de `UNKNOWN` e verificar com limites configuráveis
- [x] 1.8 Implementar reconciliação com DFIN/Informe Trimestral com warning acima do limite e verificar com teste de divergência

## 2. Aquisição CVM trimestral e DFIN

- [x] 2.1 Implementar download/extração do Informe Trimestral por CNPJ e verificar com fixture de componentes
- [x] 2.2 Preservar o código/identificador original de cada linha e verificar com teste de normalização
- [x] 2.3 Implementar download/extração das DFIN por CNPJ e verificar com fixture de valores para reconciliação
- [x] 2.4 Implementar schema versionado, reapresentações e preservação bruta (hash/metadados) e verificar com testes de schema e de múltiplas versões

## 3. Integração com métricas e análise

- [x] 3.1 Fazer `analisar_snapshot` consumir `ffo_12m`/`ffo_3m` do motor como fonte única de verdade e verificar que `FFO Yield`, `P/FFO` e `FFO Trend` são calculados
- [x] 3.2 Integrar o motor ao `FundamentalAnalysisUseCase` (componentes CVM → FFO) e verificar com teste que as métricas de FFO saem preenchidas
- [x] 3.3 Verificar que, sem componentes, as métricas de FFO saem `N/A` sem impedir as demais

## 4. Integração como fallback de FFO

- [x] 4.1 Integrar o motor de FFO à composição de fontes como fallback e verificar que é usado quando o Fundamentus não fornece FFO
- [x] 4.2 Verificar que o `FundamentusProvider` permanece como fonte primária e que os testes de FFO continuam passando

## 5. Verificação integrada

- [x] 5.1 Executar `pytest` e verificar que todos os testes passam
- [x] 5.2 Executar `ruff check` e o gate de qualidade do projeto e verificar que não há violações
- [x] 5.3 Validar a change com `openspec validate "deterministic-ffo-engine"` e verificar que é válida
