## 1. Extração no Fundamentus

- [x] 1.1 Adicionar `cotas_emitidas: Decimal | None` a `AtivoFundamental` e extrair `Nro. Cotas`/`Nro. Ações` no parser (`_ROTULOS_COTAS`, via `_primeiro`/`para_decimal`); verificar com teste unitário do parser sobre fixture de FII e de ação
- [x] 1.2 Emitir `CAMPO_COTAS_EMITIDAS` no adapter do Fundamentus (`_adicionar`); verificar com teste do provider (`tests/test_infrastructure/test_fundamentus_provider.py`)
- [x] 1.3 Atualizar as fixtures `tests/fixtures/fundamentus/` de ação e FII com `Nro. Ações`/`Nro. Cotas` e ajustar as asserções de contrato
- [x] 1.4 Elevar a versão do parser do Fundamentus para invalidar snapshots em cache sem o novo campo; verificar que o teste de cache versionado continua passando

## 2. Domínio e resolução por tipo

- [x] 2.1 Adicionar a constante `CAMPO_COTAS_EMITIDAS = "cotas_emitidas"` em `application/fundamental_ports.py` e incluí-la em `CAMPOS_FUNDAMENTAIS`; verificar que a suíte de portas continua passando
- [x] 2.2 Adicionar `cotas: Decimal | None = None` a `AnaliseFundamental` (`domain/fii/analysis.py`)
- [x] 2.3 Implementar `_resolver_cotas(dados, classificacao, patrimonio_repo)` em `FundamentalDataMixin` (FII: `patrimonio_repo.shares_outstanding` → Fundamentus; Papel: Fundamentus) e preencher `cotas` em `_analisar_ticker`; verificar com testes do caso de uso cobrindo FII com B3, FII só Fundamentus, Papel e ausência total

## 3. Apresentação

- [x] 3.1 Adicionar `formatar_quantidade` em `fundamental_formatters.py` (inteiro truncado com separador de milhar, `N/A` quando ausente); verificar com teste unitário de formatação
- [x] 3.2 Inserir `("cotas", "Nº de cotas")` em `_COLUNAS` antes de `("cotistas", "Nº de cotistas")`, adicionar `"cotas"` a `_COLUNAS_DIREITA` e emitir o valor em `_linha_analise`; verificar com teste de linhas/CSV
- [x] 3.3 Atualizar as contagens de colunas dos testes de tabela (30 totais, 2 fixas + 28 roláveis) e o cabeçalho CSV; verificar que `tests/test_presentation/test_fundamental_table.py` passa

## 4. Orientação e documentação

- [x] 4.1 Atualizar o quadro de orientações da sub-aba "Fundamentos" em `app_tabs.py` (indicadores envolvidos e como interpretar) e o `panels.md` (contagem de colunas roláveis); verificar que o teste de orientação passa
- [x] 4.2 Atualizar o `CHANGELOG.md` com a nova coluna e a política de fonte por tipo

## 5. Verificação integrada

- [x] 5.1 Executar `make lint` e `make test` e confirmar que passam sem regressões
- [x] 5.2 Validar a change com `openspec validate fundamentos-numero-cotas` e confirmar que não há erros (avisos de RFC 2119 são esperados, pois as specs do projeto usam `DEVE`)
