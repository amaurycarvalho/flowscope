## 1. Extração do documento FundosNet (B3)

- [x] 1.1 Adicionar fixture estática de um documento real de rendimentos (`tests/fixtures/b3/`) com as colunas `Rendimento | Amortização` e o rótulo `Data-base (...)` e verificar que o arquivo é lido sem rede
- [x] 1.2 Corrigir `identificar_tipo_provento`/extração para decidir o tipo pela coluna que contém o valor no layout de duas colunas, mantendo o marcador `X` como fallback, e verificar com teste unitário que o documento real retorna tipo `Rendimento`
- [x] 1.3 Corrigir a extração de `Data-base` para o rótulo com texto parentético e verificar com teste que `data_base` não é nula no documento real
- [x] 1.4 Adicionar teste de contrato que falha explicitamente quando a coluna de valor ou o rótulo de data-base some da fixture, e verificar que os testes legados (`FLAT_HTML`, `TABLE_HTML`, amortização) continuam passando

## 2. Provider de proventos e VPA no Fundamentus

- [x] 2.1 Adicionar ao cliente/parser do Fundamentus a extração da página `proventos.php?papel={TICKER}` (colunas `Data`, `Valor`, `Tipo`) e verificar com fixture estática que uma ação retorna dividendos com data-base e valor
- [x] 2.2 Implementar o `DividendHistoryProvider` do Fundamentus, tratando `DIVIDENDO`, `DIVIDENDO MENSAL`, `JRS CAP PROPRIO` e `JUROS` como rendimento e preservando a origem, e verificar com teste que amortização é ignorada e lista vazia não é erro
- [x] 2.3 Expor o indicador `VPA` como `vp_cota` quando `VP/Cota` estiver ausente e verificar com teste que uma ação com `VPA` preenche o campo e um FII continua usando `VP/Cota`

## 3. Consolidação e wiring da análise

- [x] 3.1 Injetar o provider de proventos do Fundamentus como `historico_dividendos` no controller e verificar por teste que o `FundamentalAnalysisUseCase` o utiliza na consolidação
- [x] 3.2 Verificar com teste de caso de uso que uma ação (sem histórico B3) preenche data-com, último dividendo, dividendo anterior e tendência a partir do histórico do Fundamentus
- [x] 3.3 Verificar com teste de caso de uso que um FII com proventos B3 preenche data-com, dividendo anterior e tendência e que o `Dividendo/cota` só é usado como fallback

## 4. Formatação da tabela

- [x] 4.1 Fixar `formatar_valor` em 2 casas decimais e o `Dividend Payout` em 2 casas em `fundamental_table.py` e verificar com testes que `0,7` vira `0,70`, `15,5` vira `15,50` e o payout exibe `89,40%`
- [x] 4.2 Atualizar os testes existentes de formatação que esperavam casas variáveis e verificar que a suíte de `test_fundamental_table.py` passa
- [x] 4.3 Verificar por teste que o CSV da tabela usa a mesma formatação de 2 casas exibida na tabela

## 5. Verificação integrada

- [x] 5.1 Executar `pytest` e verificar que todos os testes passam
- [x] 5.2 Executar `ruff check` e o gate de qualidade do projeto e verificar que não há violações
- [x] 5.3 Validar a change com `openspec validate "fundamentos-correcoes"` e verificar que é válida
