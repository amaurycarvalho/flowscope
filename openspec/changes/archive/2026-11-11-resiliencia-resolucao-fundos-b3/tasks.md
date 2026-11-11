# Tasks

## 1. Cliente B3 — retry de conteúdo e listagem resiliente

- [x] 1.1 Mover o parse JSON de `_get_json` para dentro do motor de retry, convertendo falha de decodificação em `requests.RequestException` e aceitando um `validar` opcional de conteúdo; verificar com teste de corpo vazio repetido que termina em resposta válida no `GetListClassFund`
- [x] 1.2 Ajustar `_PAGE_SIZE` para 120 e introduzir `ListagemFundos` (`fundos`, `completa`, `total_records`) com `obter_listagem`; manter `listar_fundos` como wrapper tolerante; verificar com testes de paginação e de lista vazia por tipo sem fundos
- [x] 1.3 Validar páginas vazias intermitentes com backoff e só gravar cache quando `len(coletados) == totalRecords`; em coleta parcial, preservar a última listagem completa; verificar com testes de página vazia repetida e de lista parcial que não sobrescreve o cache
- [x] 1.4 Versionar as chaves de listagem (`_chave_cache("fundos_listados", type_fund)`) e de resolução (`_chave_cache("fund_resolution", ticker)`) e confirmar que as chaves legadas `fundos_listados_{tipo}` e `fund_resolution_{ticker}` deixam de ser lidas; verificar com teste que cache legado parcial é ignorado
- [x] 1.5 Propagar o indicador de completude até `selecionar_candidato`/resolução de candidato, mantendo as assinaturas públicas tolerantes atuais; verificar com testes de resolução quando a listagem está completa e quando está incompleta

## 2. Store persistente de identidade

- [x] 2.1 Criar `infrastructure/b3/fund_identity_store.py` com `JsonFundIdentityStore` por ticker em `<cache>/fund_identity/<TICKER>.json`, `schema_version`, escrita atômica, leitura tolerante a ausência/corrupção/versão antiga e sem expiração; verificar com testes de gravação, leitura, corrupção e versão antiga
- [x] 2.2 Integrar o store ao `B3FundRepository.find_by_ticker`: gravar em resolução bem-sucedida, usar fallback em falha/listagem incompleta, não usar em listagem completa sem o ticker e nunca gravar negativos; verificar com testes de cada caminho
- [x] 2.3 Injetar o store no `Nucleo` e fazer `CvmAnnualFundDataProvider`/`CvmIndexadoresProvider` compartilharem o `B3FundRepository` resolvido, sem repositório isolado; verificar com teste de composição/wiring e com `make lint`
- [x] 2.4 Documentar o formato do registro, a localização `<cache>/fund_identity/<TICKER>.json` e a semântica de fallback em `docs/misc/datasources.md`; verificar que o texto descreve os campos e o comportamento implementado

## 3. Integração fiscal e verificação

- [x] 3.1 Adicionar teste de integração em que a B3 falha/incompleta, a identidade persistida fornece `idFNET` e CNPJ, e a análise fundamentalista preenche os dados fiscais do FII; verificar que o CNPJ aparece preenchido sem a B3 disponível
- [x] 3.2 Executar os testes impactados de cliente B3, repositório, store, resolução CVM e análise fundamentalista; verificar que passam
- [x] 3.3 Executar `make lint` e `make complexity`; verificar que concluem sem erros
- [x] 3.4 Repopular o cache de listagem de FIIs (530 registros esperados) e confirmar, para a watchlist, que `ALZR11`, `BTLG11`, `GGRC11`, `HGBS11`, `HSML11`, `RBVA11`, `RZTR11`, `TRXF11`, `TVRI11`, `VISC11` e `XPML11` resolvem CNPJ; verificar pela resolução real ou por inspeção do cache/store

## Workflow follow-up

- Registrar a change no CHANGELOG da release 1.8.1 via skill de changelog.
- Arquivar a change após a revisão do projeto.
- Execução manual do usuário: suíte completa (`make test`) e quality gate completo (`make quality-gate`), se desejar, por precaução.
