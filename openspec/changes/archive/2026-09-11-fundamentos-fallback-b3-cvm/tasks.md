## 0. Pré-requisito de coordenação

- [x] 0.1 Confirmar que `fundamentos-informacoes-adicionais-fiscais` já foi aplicada (campos fiscais no informe B3, `get_indexadores`, campos adicionais e colunas novas) antes de iniciar; verificar pela presença dos campos/métodos no código
- [x] 0.2 Confirmar que esta change não remove nem renomeia os campos fiscais/adicionais nem as colunas `Informações adicionais`/`Dados fiscais`; verificar com a suíte existente após os acréscimos

## 1. Extração da classificação do Informe Mensal da B3

- [x] 1.1 Adicionar campos de classificação autorregulação (`classificacao`, `subclassificacao`, `gestao`, `segmento_atuacao`) a `B3InformeMensal` e extraí-los por rótulo em `extrair_informe_mensal`, tolerando rótulos ausentes; verificar com teste do parser sobre fixture do informe de `CYCR11` (Classificação `Papel`, Gestão `Ativa`, Segmento `Outros`)
- [x] 1.2 Garantir que a ausência do rótulo não invalida os demais campos; verificar com teste de informe sem classificação retornando `None` nos novos campos e mantendo cotistas/patrimônio
- [x] 1.3 Expor a classificação extraída no fluxo `B3FundamentalRepository`/`B3FundamentalDataProvider`; verificar com teste do provider devolvendo `CAMPO_CLASSIFICACAO_FII`, `CAMPO_DISCRIMINADOR`, `CAMPO_SEGMENTO` e `CAMPO_GESTAO` (o `CAMPO_QTD_IMOVEIS` não é emitido pela B3; ver 6.2)

## 2. VP/Cota e proveniência no provider B3

- [x] 2.1 Emitir `CAMPO_VP_COTA` a partir de `PatrimonioFii.vp_cota` e derivar `net_asset_value / shares_outstanding` quando o reportado for ausente; verificar com teste de B3 com e sem `vp_cota`
- [x] 2.2 Memorizar `obter_patrimonio` por `(ticker, reference_date)` em `B3FundamentalRepository` para evitar dupla busca entre provider e caso de uso; verificar com teste que conta chamadas à fonte
- [x] 2.3 Verificar que a proveniência (`CampoFundamental.fonte`) permanece `B3` nos novos campos compostos; verificar com teste do `CompositeFundamentalProvider`

## 3. Caso de uso: cotação, data de referência e P/L

- [x] 3.1 Preencher `cotacao` com `self._mercado.preco_fechamento(...)` quando o Fundamentus não fornecer, reaproveitando o `PrecoObservacao` já usado nas métricas; verificar com teste de ticker sem Fundamentus exibindo `P (Cotação)`
- [x] 3.2 Preencher `data_referencia` com a data do fechamento B3 quando o Fundamentus não informar; verificar com teste que a data exibida é a do último fechamento
- [x] 3.3 Confirmar que `P/L` é derivado quando `cotacao` e classificação FII estão presentes e permanece `N/A` caso contrário; verificar com teste do `CYCR11` derivando `P/L` de `preco / (ultimo_dividendo × 12)`
- [x] 3.4 Garantir que `Tipo`/`Sub-tipo` exibem `FII` / `Papel: Outros, Ativa` para `CYCR11` via classificação da B3; verificar com teste da linha da tabela
- [x] 3.5 Preencher `Min 52 sem`/`Max 52 sem` com os extremos da janela B3 em cache (`daily_data`, ≤ 52 semanas) quando o Fundamentus não fornecer, sem novo acesso; verificar com teste de ticker sem Fundamentus calculando `Preço Típico`/`P / PT` e com janela vazia resultando `N/A`

## 4. Elegibilidade do motor determinístico de FFO

- [x] 4.1 Restringir o acionamento de `_analisar_ffo` a FII de tijolo/híbrido, derivando a classe efetiva dos campos compostos; verificar com teste de FII de papel sem Fundamentus exibindo `FFO Yield`, `P/FFO` e `FFO Trend` como `N/A`
- [x] 4.2 Verificar que FII de tijolo/híbrido continua acionando o motor e que o FFO reportado pelo Fundamentus permanece inalterado para papel; verificar com testes de integração do caso de uso

## 5. CvmQuarterlyRepository: layout largo

- [x] 5.1 Detectar o layout largo (`CNPJ_Fundo_Classe` + `Data_Referencia` + colunas de resultado, sem `Descricao`/`Valor`) em `_ler_registros`, reutilizando o carregamento do ZIP e a seleção de competência já usados por `get_indexadores`, e não levantar erro de schema; verificar com teste sobre amostra real de `inf_trimestral_fii_resultado_contabil_financeiro_2026.csv`
- [x] 5.2 Converter cada coluna monetária aplicável em componente com `codigo` = coluna original e `descricao` legível; verificar que `Receita_Aluguel_Investimento_Contabil` vira componente `RECURRING`
- [x] 5.3 Manter o layout longo legado funcionando; verificar com o teste existente de `get_components`
- [x] 5.4 Verificar que `FFOEngineProvider` calcula FFO para um CNPJ de tijolo com o layout real e retorna `None` quando faltam componentes

## 6. Cobertura de fallback e cache

- [x] 6.1 Garantir que as colunas sem fallback (`LPA`/`ROE`/`ROIC`, `Qtd Imóveis`/`Cap Rate`/`Vacância Média`) permaneçam `N/A` quando o Fundamentus não fornece o dado; verificar com teste de ticker sem Fundamentus mantendo as demais colunas preenchidas
- [x] 6.2 Resolver a inconsistência do `CAMPO_QTD_IMOVEIS` (task 1.3/D2): derivá-lo da classificação autorregulação da B3 (Tijolo/Híbrido → imóveis) ou remover a menção das tasks/design; verificar que `classificar_exibicao` produz `Tijolo:`/`Papel:` para `CYCR11`
- [x] 6.3 Confirmar que Papel sem Fundamentus mantém `P/L`, `Dividend Yield` e as colunas de dividendo como `N/A` (limite documentado), sem impedir as demais colunas
- [x] 6.4 Memoizar o parse normalizado do Informe Trimestral/Anual da CVM ou registrar em `design.md` que o cache de arquivo bruto é suficiente; verificar com teste de contagem de parsing por ticker

## 7. Verificação final

- [x] 7.1 Rodar `ruff check` e a suíte de testes afetada (`pytest tests/test_infrastructure tests/test_application tests/test_domain`) e verificar que não há regressões
- [x] 7.2 Validar a change com `openspec validate fundamentos-fallback-b3-cvm` (modo não-estrito; `--strict` falha apenas nos avisos pré-existentes de RFC 2119 da convenção em português)
- [x] 7.3 Conferir a saída da tabela/CSV para a watchlist de exemplo com `CYCR11` preenchido e demais tickers inalterados
