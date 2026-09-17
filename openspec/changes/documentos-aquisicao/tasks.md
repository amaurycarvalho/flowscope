## 1. Pré-requisito

- [x] 1.1 Confirmar que `DocumentosRelevantesProvider`, `InformeMensalArquivoProvider`, `listar_fatos_relevantes` e o download CVM (`ExibirPDF`) já existem e são reutilizáveis
- [x] 1.2 Confirmar que `DocumentCatalog` e a sub-aba "Documentos" (change `visualizacao-documentos`) permanecem somente-leitura e sem requisitos alterados

## 2. Download CVM compartilhado

- [x] 2.1 Extrair o download de PDF da CVM (POST `ExibirPDF` com `numeroProtocolo`, base64 e validação `%PDF`) para um helper reutilizável em `infrastructure/cvm/`, verificando com teste que PDF válido retorna bytes e conteúdo não-PDF retorna `None`
- [x] 2.2 Fazer `BdrClient.baixar_pdf` delegar ao helper, verificando que os testes existentes de BDR continuam passando

## 3. Orquestrador de aquisição

- [x] 3.1 Implementar `AquisicaoDocumentos.adquirir(ticker, reference_date)` com detecção de tipo (`resolver_ticker` → FII; `resolver_code_cvm` → ação/BDR) e sem download quando a identidade não resolve, verificando com teste que ticker não resolvido não dispara download
- [x] 3.2 Implementar a aquisição de material facts (fatos relevantes e assembleias) listando, baixando o PDF da CVM e gravando em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, verificando com teste de gravação e mapeamento de slug
- [x] 3.3 Implementar a aquisição de FIIs (documentos relevantes das 4 categorias e informe mensal mais recente), verificando com teste que os PDFs e o HTML são gravados nas árvores corretas
- [x] 3.4 Garantir reuso de cache sem novo download e tolerância a falha individual, verificando com teste de cache hit e de falha de rede sem arquivo criado

## 4. Acionamento no painel e na interface

- [x] 4.1 Adicionar `acquire_callback` opcional ao `DocumentTreePanel` (acionado em `update`/refresh quando definido) mantendo a varredura pura quando ausente, verificando com teste do painel
- [x] 4.2 Acionar a aquisição em thread de trabalho na GUI, com estado de carregamento e remontagem da árvore na thread do Tk ao concluir, verificando com teste de integração do acionamento
- [x] 4.3 Usar o ticker apresentado (sincronizado com "Evolução dos Fundamentos") na aquisição, verificando com teste de que ambas as sub-abas recebem o mesmo ticker

## 5. Testes de integração

- [x] 5.1 Testar a orquestração ponta a ponta com cliente e download mockados (ação e FII), verificando os arquivos criados
- [x] 5.2 Testar que falha de aquisição mantém a árvore utilizável e exibe o estado vazio sem erro

## 6. Quality Gate

- [x] 6.1 Executar `make lint` e corrigir avisos/erros introduzidos
- [x] 6.2 Executar `make test` e garantir que todos os testes passam
- [x] 6.3 Executar `openspec validate documentos-aquisicao` e garantir que a change permanece válida

## 7. Ajustes de comportamento da sub-aba

- [x] 7.1 Fazer `update` do painel apenas ler o catálogo de cache (sem aquisição) e mover o acionamento para o botão "Atualizar"; verificar com teste que abrir não dispara o callback e "Atualizar" dispara
- [x] 7.2 Unificar a janela de aquisição em 12 meses (documentos relevantes, material facts e informe mensal) com reuso de cache; verificar com teste do início da janela
- [x] 7.3 Renomear o botão para "Abrir documento" e habilitá-lo somente com um documento selecionado; verificar com testes de estado do botão

## 8. Progresso e bloqueio da interface no "Atualizar"

- [x] 8.1 Reportar progresso por documento em `AquisicaoDocumentos.adquirir` (callback opcional) e publicar mensagens de progresso no `DocumentosJob`; verificar com teste de progresso
- [x] 8.2 Na GUI, desabilitar os botões, ativar o cursor de espera e atualizar barra de status/progresso durante o "Atualizar", com guard de reentrância e restauração ao término; verificar com teste de integração
- [x] 8.3 Alinhar o requisito de abertura do `documentos-ticker-panel` (change `visualizacao-documentos`) ao botão "Abrir documento"; verificar com `openspec validate`

## 9. Bloqueio global do botão "Atualizar"

- [x] 9.1 Expor `refresh_button()` no `DocumentTreePanel` e incluí-lo em `_disable_all_buttons`/`_restore_all_buttons`; verificar com teste que o botão é desabilitado e restaurado
- [x] 9.2 Remover o `set_busy` local (substituído pelo bloqueio global) e ajustar os testes; verificar com a suíte

## 10. Bloqueio global do botão "Abrir documento"

- [x] 10.1 Expor `all_buttons()` no `DocumentTreePanel` (incluindo "Abrir documento") e integrá-lo ao bloqueio global; reavaliar o estado pela seleção ao restaurar (`refresh_open_button`); verificar com testes
- [x] 10.2 Atualizar os testes de estado do painel e de bloqueio global; verificar com `make test` e `make lint`

## 11. Correção da resolução codeCVM e do material facts (ações)

- [x] 11.1 Corrigir `resolver_code_cvm` para consultar `GetInitialCompanies` filtrando por `company=<raiz>` e casar `issuingCompany`, com paginação e chave de cache versionada; verificar com testes de PETR4, homônimos, paginação e `None`
- [x] 11.2 Corrigir o payload do `GetMaterialFacts` para `language`/`dateInitial`/`dateFinal`/`category`; verificar com os testes do cliente de material facts
- [x] 11.3 Validar a aquisição ponta a ponta na API real para AGRO3, BBAS3, BRAP3, PETR3 e VALE3, confirmando os PDFs em `documentos-relevantes/`
- [x] 11.4 Registrar as correções nas specs `code-cvm-resolution` e `material-facts-extraction` e nos artefatos desta change; verificar com `openspec validate documentos-aquisicao`

## 12. Timeout limitado nos documentos do FundosNet (FIIs)

- [x] 12.1 Adicionar `_TIMEOUT_DOCUMENTO` e usá-lo em `baixar_pdf_documento` e `buscar_html_documento`; verificar com testes de que o timeout curto é aplicado
- [x] 12.2 Verificar que um `ReadTimeout` isolado é retentado até o sucesso; verificar com teste de callback que falha uma vez e responde na segunda
- [x] 12.3 Validar a aquisição ponta a ponta na API real para KNCA11, KNCR11, BBGO11 e BTLG11, confirmando os PDFs em `documentos-relevantes/` sem travamento
