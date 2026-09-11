## 0. Pré-requisito de coordenação

- [ ] 0.1 Confirmar que `fundamentos-informacoes-adicionais-fiscais` já foi aplicada (campos fiscais no informe B3, `get_indexadores`, campos adicionais e colunas novas) antes de iniciar; verificar pela presença dos campos/métodos no código
- [ ] 0.2 Confirmar que esta change não remove nem renomeia os campos fiscais/adicionais nem as colunas `Informações adicionais`/`Dados fiscais`; verificar com a suíte existente após os acréscimos

## 1. Extração da classificação do Informe Mensal da B3

- [ ] 1.1 Adicionar campos de classificação autorregulação (`classificacao`, `subclassificacao`, `gestao`, `segmento_atuacao`) a `B3InformeMensal` e extraí-los por rótulo em `extrair_informe_mensal`, tolerando rótulos ausentes; verificar com teste do parser sobre fixture do informe de `CYCR11` (Classificação `Papel`, Gestão `Ativa`, Segmento `Outros`)
- [ ] 1.2 Garantir que a ausência do rótulo não invalida os demais campos; verificar com teste de informe sem classificação retornando `None` nos novos campos e mantendo cotistas/patrimônio
- [ ] 1.3 Expor a classificação extraída no fluxo `B3FundamentalRepository`/`B3FundamentalDataProvider`; verificar com teste do provider devolvendo `CAMPO_CLASSIFICACAO_FII`, `CAMPO_DISCRIMINADOR`, `CAMPO_SEGMENTO`, `CAMPO_GESTAO` e `CAMPO_QTD_IMOVEIS`

## 2. VP/Cota e proveniência no provider B3

- [ ] 2.1 Emitir `CAMPO_VP_COTA` a partir de `PatrimonioFii.vp_cota` e derivar `net_asset_value / shares_outstanding` quando o reportado for ausente; verificar com teste de B3 com e sem `vp_cota`
- [ ] 2.2 Memorizar `obter_patrimonio` por `(ticker, reference_date)` em `B3FundamentalRepository` para evitar dupla busca entre provider e caso de uso; verificar com teste que conta chamadas à fonte
- [ ] 2.3 Verificar que a proveniência (`CampoFundamental.fonte`) permanece `B3` nos novos campos compostos; verificar com teste do `CompositeFundamentalProvider`

## 3. Caso de uso: cotação, data de referência e P/L

- [ ] 3.1 Preencher `cotacao` com `self._mercado.preco_fechamento(...)` quando o Fundamentus não fornecer, reaproveitando o `PrecoObservacao` já usado nas métricas; verificar com teste de ticker sem Fundamentus exibindo `P (Cotação)`
- [ ] 3.2 Preencher `data_referencia` com a data do fechamento B3 quando o Fundamentus não informar; verificar com teste que a data exibida é a do último fechamento
- [ ] 3.3 Confirmar que `P/L` é derivado quando `cotacao` e classificação FII estão presentes e permanece `N/A` caso contrário; verificar com teste do `CYCR11` derivando `P/L` de `preco / (ultimo_dividendo × 12)`
- [ ] 3.4 Garantir que `Tipo`/`Sub-tipo` exibem `FII` / `Papel: Outros, Ativa` para `CYCR11` via classificação da B3; verificar com teste da linha da tabela

## 4. Elegibilidade do motor determinístico de FFO

- [ ] 4.1 Restringir o acionamento de `_analisar_ffo` a FII de tijolo/híbrido, derivando a classe efetiva dos campos compostos; verificar com teste de FII de papel sem Fundamentus exibindo `FFO Yield`, `P/FFO` e `FFO Trend` como `N/A`
- [ ] 4.2 Verificar que FII de tijolo/híbrido continua acionando o motor e que o FFO reportado pelo Fundamentus permanece inalterado para papel; verificar com testes de integração do caso de uso

## 5. CvmQuarterlyRepository: layout largo

- [ ] 5.1 Detectar o layout largo (`CNPJ_Fundo_Classe` + `Data_Referencia` + colunas de resultado, sem `Descricao`/`Valor`) em `_ler_registros`, reutilizando o carregamento do ZIP e a seleção de competência já usados por `get_indexadores`, e não levantar erro de schema; verificar com teste sobre amostra real de `inf_trimestral_fii_resultado_contabil_financeiro_2026.csv`
- [ ] 5.2 Converter cada coluna monetária aplicável em componente com `codigo` = coluna original e `descricao` legível; verificar que `Receita_Aluguel_Investimento_Contabil` vira componente `RECURRING`
- [ ] 5.3 Manter o layout longo legado funcionando; verificar com o teste existente de `get_components`
- [ ] 5.4 Verificar que `FFOEngineProvider` calcula FFO para um CNPJ de tijolo com o layout real e retorna `None` quando faltam componentes

## 6. Verificação final

- [ ] 6.1 Rodar `ruff check` e a suíte de testes afetada (`pytest tests/test_infrastructure tests/test_application tests/test_domain`) e verificar que não há regressões
- [ ] 6.2 Validar a change com `openspec validate fundamentos-fallback-b3-cvm --strict`
- [ ] 6.3 Conferir a saída da tabela/CSV para a watchlist de exemplo com `CYCR11` preenchido e demais tickers inalterados
