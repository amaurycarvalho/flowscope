## 1. Pré-requisito

- [ ] 1.1 Confirmar que `DocumentosRelevantesProvider`, `InformeMensalArquivoProvider`, `listar_fatos_relevantes` e o download CVM (`ExibirPDF`) já existem e são reutilizáveis
- [ ] 1.2 Confirmar que `DocumentCatalog` e a sub-aba "Documentos" (change `visualizacao-documentos`) permanecem somente-leitura e sem requisitos alterados

## 2. Download CVM compartilhado

- [ ] 2.1 Extrair o download de PDF da CVM (POST `ExibirPDF` com `numeroProtocolo`, base64 e validação `%PDF`) para um helper reutilizável em `infrastructure/cvm/`, verificando com teste que PDF válido retorna bytes e conteúdo não-PDF retorna `None`
- [ ] 2.2 Fazer `BdrClient.baixar_pdf` delegar ao helper, verificando que os testes existentes de BDR continuam passando

## 3. Orquestrador de aquisição

- [ ] 3.1 Implementar `AquisicaoDocumentos.adquirir(ticker, reference_date)` com detecção de tipo (`resolver_ticker` → FII; `resolver_code_cvm` → ação/BDR) e sem download quando a identidade não resolve, verificando com teste que ticker não resolvido não dispara download
- [ ] 3.2 Implementar a aquisição de material facts (fatos relevantes e assembleias) listando, baixando o PDF da CVM e gravando em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, verificando com teste de gravação e mapeamento de slug
- [ ] 3.3 Implementar a aquisição de FIIs (documentos relevantes das 4 categorias e informe mensal mais recente), verificando com teste que os PDFs e o HTML são gravados nas árvores corretas
- [ ] 3.4 Garantir reuso de cache sem novo download e tolerância a falha individual, verificando com teste de cache hit e de falha de rede sem arquivo criado

## 4. Acionamento no painel e na interface

- [ ] 4.1 Adicionar `acquire_callback` opcional ao `DocumentTreePanel` (acionado em `update`/refresh quando definido) mantendo a varredura pura quando ausente, verificando com teste do painel
- [ ] 4.2 Acionar a aquisição em thread de trabalho na GUI, com estado de carregamento e remontagem da árvore na thread do Tk ao concluir, verificando com teste de integração do acionamento
- [ ] 4.3 Usar o ticker apresentado (sincronizado com "Evolução dos Fundamentos") na aquisição, verificando com teste de que ambas as sub-abas recebem o mesmo ticker

## 5. Testes de integração

- [ ] 5.1 Testar a orquestração ponta a ponta com cliente e download mockados (ação e FII), verificando os arquivos criados
- [ ] 5.2 Testar que falha de aquisição mantém a árvore utilizável e exibe o estado vazio sem erro

## 6. Quality Gate

- [ ] 6.1 Executar `make lint` e corrigir avisos/erros introduzidos
- [ ] 6.2 Executar `make test` e garantir que todos os testes passam
- [ ] 6.3 Executar `openspec validate documentos-aquisicao` e garantir que a change permanece válida
