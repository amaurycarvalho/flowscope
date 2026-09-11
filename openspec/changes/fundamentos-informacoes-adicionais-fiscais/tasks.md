## 1. Ingestão do INF_ANUAL da CVM

- [ ] 1.1 Criar o fluxo anual da CVM sobre o `CvmDatasetDownloader` (`FII/DOC/INF_ANUAL`, `dataset=FII-INF-ANUAL`) e verificar o download/cache com fixture de ZIP anual
- [ ] 1.2 Implementar `CvmAnnualRepository.get(cnpj, reference_date)` filtrando por CNPJ e competência e selecionando o registro mais recente; verificar com teste de CNPJ presente, ausente e competência futura
- [ ] 1.3 Normalizar gestor (nome/CNPJ), administrador (nome/CNPJ), custodiante e auditor, tratando vazios como ausência; verificar com teste de registro completo e com campos ausentes
- [ ] 1.4 Verificar a reutilização do arquivo local e o registro de hash/versão nos metadados; verificar com teste de segundo acesso sem novo fetch

## 2. Identidade fiscal do Informe Mensal da B3

- [ ] 2.1 Adicionar `cnpj`, `nome_administrador` e `cnpj_administrador` a `B3InformeMensal` e extraí-los por rótulo em `extrair_informe_mensal`; verificar com fixture do informe de `CYCR11`
- [ ] 2.2 Emitir `CAMPO_CNPJ`, `CAMPO_ADMINISTRADOR` e `CAMPO_CNPJ_ADMINISTRADOR` no `B3FundamentalDataProvider`; verificar com teste do provider e da proveniência `B3`

## 3. Campos adicionais no Fundamentus

- [ ] 3.1 Adicionar `CAMPO_LPA`, `CAMPO_ROE`, `CAMPO_ROIC`, `CAMPO_CAP_RATE` e `CAMPO_VACANCIA_MEDIA` em `fundamental_ports.py` e mapeá-los em `campos_do_ativo`; verificar com teste do adapter para ação (`LPA`/`ROE`/`ROIC`) e FII (`Cap Rate`/`Vacância Média`)
- [ ] 3.2 Verificar que indicador ausente ou `-` não é exposto, sem afetar os demais; verificar com teste de `ROIC = -`

## 4. Preço Típico e percentuais por indexador

- [ ] 4.1 Implementar `preco_tipico` e `percentual_preco_tipico` em `domain/fii/metrics.py`; verificar com testes de cálculo e de insumo ausente/zero
- [ ] 4.2 Implementar `CvmQuarterlyRepository.get_indexadores(cnpj, reference_date)` lendo o `complemento`; verificar com teste de competência mais recente e de ausência
- [ ] 4.3 Expor `preco_tipico`, `pct_preco_tipico` e os percentuais por indexador em `AnaliseFundamental`/`_analisar_ticker`; verificar com teste do caso de uso

## 5. Colunas Informações adicionais e Dados fiscais

- [ ] 5.1 Adicionar os dois ids ao final de `_COLUNAS` e montar `Informações adicionais` para Papel (LPA/ROE/ROIC/Preço Típico/%Preço Típico) e FII (imóveis/Preço Típico/indexadores), omitindo itens ausentes; verificar com testes de linha da tabela
- [ ] 5.2 Omitir `Qtd Imóveis`/`Cap Rate`/`Vacância Média` quando `qtd_imoveis` for zero ou desconhecido; verificar com teste de FII de papel e de FII sem Fundamentus
- [ ] 5.3 Montar `Dados fiscais` com `CNPJ`, `Administrador (CNPJ)` e `Gestor (CNPJ)` para FII e apenas `CNPJ` para Papel, omitindo ausentes e exibindo `N/A` quando vazio; verificar com testes
- [ ] 5.4 Verificar que o CSV (`montar_csv`) inclui as duas colunas com os mesmos textos; verificar com teste de exportação

## 6. Verificação final

- [ ] 6.1 Rodar `ruff check` e a suíte afetada (`pytest tests/test_infrastructure tests/test_application tests/test_domain tests/test_presentation`) sem regressões
- [ ] 6.2 Validar a change com `openspec validate fundamentos-informacoes-adicionais-fiscais --strict`
- [ ] 6.3 Conferir a saída da tabela/CSV para uma watchlist com Papel, FII de tijolo e FII de papel, garantindo omissões e `N/A` corretos
