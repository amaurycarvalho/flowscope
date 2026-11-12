# Tasks

## 1. Extração do Informe Mensal

- [x] 1.1 Adicionar `nome_gestor` e `cnpj_gestor` a `B3InformeMensal` em `domain/b3/models.py` e verificar que os valores default permanecem `None`
- [x] 1.2 Ampliar `_ROTULOS_CNPJ` em `infrastructure/b3/informe_mensal_parser.py` para aceitar `cnpjdofundo` além de `cnpjdofundoclasse` e adicionar os rótulos de gestor (`nomedogestor`, `cnpjdogestor`); verificar com fixture de informe FIAGRO contendo `CNPJ do Fundo`, `Nome do Gestor` e `CNPJ do Gestor`
- [x] 1.3 Adicionar fixture de informe FIAGRO (ex.: `tests/fixtures/b3/informe_fiagro.html`) baseada no informe real de `KNCA11` e verificar que o parser extrai CNPJ `41745701000137`, administrador, gestor e os demais campos sem regressão
- [x] 1.4 Estender os testes de `TestInformeMensalParser` para a variante `CNPJ do Fundo` e para gestor, mantendo o cenário de rótulo ausente sem invalidar os demais campos; verificar com `pytest tests/test_infrastructure/test_b3_acquisition.py -k InformeMensalParser`

## 2. Reuso do cache persistente de idFNET/CNPJ

- [x] 2.1 Expor em `B3FundamentalRepository` a identidade resolvida (ou o CNPJ) obtida pelo `B3FundRepository`, que já consulta `JsonFundIdentityStore`, e verificar com teste que, com a listagem B3 indisponível/incompleta e o store preenchido, a identidade persistida é retornada
- [x] 2.2 Verificar que `B3FundamentalRepository.obter_informe` usa o `idFNET` persistido quando a listagem de fundos falha; cobrir com teste que injeta cliente B3 indisponível e store com `id_fnet`, sem novo cache
- [x] 2.3 Garantir que o store existente continua sendo gravado apenas em resolução bem-sucedida e que nenhum schema/arquivo novo é criado; executar `pytest tests/test_infrastructure/test_fund_identity_store.py`
- [x] 2.4 Versionar a chave da listagem de documentos e repetir uma vez a primeira página vazia, sem persistir vazio persistente; verificar com testes de vazio intermitente e de vazio sempre presente em `test_b3_acquisition.py`

## 3. Provider fundamentalista B3

- [x] 3.1 Emitir `CAMPO_GESTOR` e `CAMPO_CNPJ_GESTOR` a partir do informe em `infrastructure/fii/b3_fundamental_provider.py`, com fonte `B3`; verificar com teste de `TestB3FundamentalDataProvider` que os campos saem preenchidos
- [x] 3.2 Emitir `CAMPO_CNPJ` a partir do informe e, quando ausente, da identidade persistida (idFNET/CNPJ), mantendo o informe como prioritário; verificar com testes dos dois cenários
- [x] 3.3 Verificar que o provider continua emitindo CNPJ e administrador e que campos ausentes não são expostos; verificar com os testes do provider em `tests/test_infrastructure/test_b3_acquisition.py`

## 4. Integração e regressão

- [x] 4.1 Adicionar teste de composição em que o provider B3 fornece a identidade fiscal completa de um FIAGRO e verificar que `CompositeFundamentalProvider` expõe CNPJ, administrador e gestor com origem `B3`
- [x] 4.2 Verificar que o fallback `CvmAnnualFundDataProvider` ainda preenche o gestor quando a B3 não o fornece; executar `pytest tests/test_application/test_fundamental_identity_fallback.py`
- [x] 4.3 Verificar que uma análise de `KNCA11` com informe FIAGRO em cache passa a preencher `cnpj`, `nome_administrador`, `cnpj_administrador`, `nome_gestor` e `cnpj_gestor`; registrar a verificação no teste de integração
- [x] 4.4 Verificar o cenário em que o informe não está disponível mas a identidade persistida de `KNCA11` existe: o CNPJ fiscal é preenchido pelo cache de idFNET e administrador/gestor ficam ausentes sem erro
- [x] 4.5 Verificar sobre os dados reais que, após descartar a listagem vazia, `obter_informe("KNCA11")` retorna o informe `1350966` com administrador `INTRAG DTVM LTDA.` e gestor `KINEA INVESTIMENTOS LTDA`

## 5. Quality gate da change

- [x] 5.1 Executar `make lint` e verificar que conclui sem erros
- [x] 5.2 Executar `make complexity` e verificar que conclui sem erros
- [x] 5.3 Executar os testes impactados (`tests/test_infrastructure/test_b3_acquisition.py`, `tests/test_infrastructure/test_fund_identity_store.py` e `tests/test_application/test_fundamental_identity_fallback.py`) e verificar que passam

## Workflow follow-up

- Reexecutar a análise de `KNCA11` com `force_refresh` (“Atualizar fundamentos” ou CLI de atualização) para regravar a observação do dia sem administrador/gestor e confirmar os campos na tabela. A leitura normal do mesmo dia continua servindo o registro imutável antigo.
- Confirmar que a chave antiga `fund_docs_...` vazia é ignorada e que a nova chave versionada grava a listagem com os documentos.
- Arquivar a change após a revisão e a aprovação do projeto.
- Verificar o resultado arquivado em `openspec/specs/`.
