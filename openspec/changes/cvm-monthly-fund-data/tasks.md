## 1. Modelos e schema CVM

- [ ] 1.1 Criar modelos de aquisição CVM (`FundIdentity`, `MonthlyReport` com `raw_rows`, `source_file`, `source_hash`) e verificar com teste unitário a normalização do CNPJ
- [ ] 1.2 Implementar resolução de colunas por aliases (`CNPJ_Fundo_Classe`/`CNPJ_Fundo`, `QT_COTA`/`QUANT_COTA`) e verificar com testes de schema atual e legado
- [ ] 1.3 Levantar erro de schema quando colunas obrigatórias faltarem e verificar com teste que a falha é explícita

## 2. Download, extração e cache

- [ ] 2.1 Implementar download do ZIP anual e extração dos CSVs com `zipfile`+`csv` (stdlib) e verificar com teste que lista todos os `.csv` do arquivo
- [ ] 2.2 Calcular e registrar SHA-256 e metadados do arquivo bruto sob `~/.cache/flowscope/cvm/inf_mensal/<ano>/` e verificar que o hash é gravado
- [ ] 2.3 Implementar cache por dataset+ano+hash e verificar que o download não é repetido quando o hash não mudou

## 3. Filtro, identidade e reapresentações

- [ ] 3.1 Implementar filtro por CNPJ normalizado e competência, validando a identidade, e verificar com fixture de registros do fundo
- [ ] 3.2 Implementar seleção da reapresentação mais recente com `is_latest` e versão de origem, verificando com fixture de múltiplas versões
- [ ] 3.3 Implementar a resolução `ticker → CNPJ` (B3 `tradingName` + cadastro CVM) e verificar com teste de ticker resolvido e não resolvido

## 4. Integração com a análise fundamentalista

- [ ] 4.1 Normalizar `PatrimonioFii` (PL, cotas, cotistas) a partir do registro selecionado e verificar com teste de valores esperados
- [ ] 4.2 Fazer o `CvmFiiAdapter`/`FundamentalRepository` consumir o novo repositório, verificando que o contrato `PatrimonioFii` é preservado
- [ ] 4.3 Preencher `P/VP` no `FundamentalAnalysisUseCase` quando houver patrimônio e preço, verificando com teste que `P/VP` sai calculado e que FFO permanece `N/A`

## 5. Verificação integrada

- [ ] 5.1 Executar `pytest` e verificar que todos os testes passam
- [ ] 5.2 Executar `ruff check` e o gate de qualidade do projeto e verificar que não há violações
- [ ] 5.3 Validar a change com `openspec validate "cvm-monthly-fund-data"` e verificar que é válida
