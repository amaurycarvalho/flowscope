## 1. Campos novos no domínio e aplicação

- [x] 1.1 Adicionar `cotacao` e `vp_cota` (`Decimal | None`) a `AnaliseFundamental` e preenchê-los em `FundamentalAnalysisUseCase._analisar_ticker` a partir de `CAMPO_COTACAO` e `CAMPO_VP_COTA`; verificar com teste que os campos são propagados quando presentes e `None` quando ausentes
- [x] 1.2 Adicionar a chave `CAMPO_VP_COTA` em `application/fundamental_ports.py` e incluí-la em `CAMPOS_FUNDAMENTAIS`; verificar que a constante existe e é consumida pela composição de fontes
- [x] 1.3 Mapear o indicador `VP/Cota` para `CAMPO_VP_COTA` no adapter do Fundamentus; verificar com teste de contrato sobre a fixture `tests/fixtures/fundamentus/fii_visc11.html` que o campo é exposto

## 2. Classificação

- [x] 2.1 Alterar `_juntar` em `domain/fii/classification.py` para separar por `", "`; verificar `pytest tests/test_presentation/test_fundamental_table.py -k ClassificacaoExibicao` verde com os rótulos atualizados

## 3. Tabela fundamentalista

- [x] 3.1 Reordenar `_COLUNAS` e incluir `dividendo_anterior`, `dividend_payout`, `p` e `vp` nas posições definidas; verificar `montar_csv` com o novo cabeçalho
- [x] 3.2 Preencher as novas colunas em `_linha_analise` (dividendo anterior, `DY/FFOY`, P, VP) e manter `N/A` em `_linha_sintetica`; verificar teste de `montar_linhas`
- [x] 3.3 Aplicar `anchor="e"` nas 11 colunas numéricas no `FundamentalTablePanel`; verificar com teste (sob `DISPLAY`) que `tree.column(id, "anchor") == "e"` e as textuais permanecem à esquerda
- [x] 3.4 Atualizar `tests/test_presentation/test_fundamental_table.py` (índices das colunas e cabeçalho do CSV); verificar `pytest tests/test_presentation/test_fundamental_table.py` verde

## 4. Verificação final

- [x] 4.1 Rodar `ruff check` e a suíte de testes afetada; verificar que não há regressões
