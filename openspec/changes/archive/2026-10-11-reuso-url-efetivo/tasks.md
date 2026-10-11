## 1. Deduplicação expõe o canônico

- [x] 1.1 Adicionar `DeduplicacaoConteudo.processar_e_resolver` devolvendo `(gravado, relativo_canonico)` e reexpressar `processar` como invólucro; verificar com testes em `tests/test_application/test_deduplicacao.py`.

## 2. Documentos

- [x] 2.1 Registrar a URL no descarte por duplicidade em `_persistir_material_fact` (ações/BDRs), apontando ao canônico; verificar que uma segunda execução não baixa de novo, mesmo com data diferente, em `tests/test_infrastructure/test_documentos_aquisicao.py`.
- [x] 2.2 Registrar a URL no descarte por duplicidade em `DocumentosRelevantesProvider.persistir` (FIIs); verificar em `tests/test_infrastructure/test_documentos_relevantes.py`.

## 3. Notícias

- [x] 3.1 Registrar a URL no descarte por duplicidade em `AquisicaoNoticias._persistir`, indexando o canônico; verificar reuso entre execuções em `tests/test_infrastructure/test_regulacao/test_noticias_aquisicao.py`.

## 4. Verificação integrada

- [x] 4.1 Rodar `pytest` (marker padrão) e confirmar que a suíte passa.
- [x] 4.2 Rodar a verificação das specs: `openspec validate reuso-url-efetivo`.
- [x] 4.3 Rodar `make complexity` e o lint para confirmar os gates.
