## 1. Domínio

- [x] 1.1 Criar `domain/documents/entities.py` com `DocumentoArquivo`, `CategoriaDocumentos`, `MesDocumentos`, `AnoDocumentos` e `CatalogoTicker`; verificar com testes de entidade (igualdade imutável e propriedade `vazio`)
- [x] 1.2 Atualizar os importadores para as entidades de domínio; verificar `make test` verde sem mudança de comportamento

## 2. Aplicação

- [x] 2.1 Criar a porta `CatalogoRepository`, o read-model `montar_catalogo`/ordenação e `chave_documento` em `application`; verificar com testes puros de agrupamento, ordenação e chave estável
- [x] 2.2 Criar a porta `DocumentSummaryStore` em `application` espelhando `DocumentTextStore`; verificar com teste de contrato em `tests/test_application`
- [x] 2.3 Mover `DocumentSummaryService` e `GuidanceService` de `presentation/gui/charts/` para `application`, incluindo `DocumentSummaryService.atualizar` (reflete sem gravar); verificar seus testes rodando sem Tk

## 3. Infraestrutura

- [x] 3.1 Fazer `infrastructure/document_catalog.py` implementar `CatalogoRepository` (varredura de filesystem) usando as entidades de domínio; verificar `test_document_catalog.py` migrado para o novo contrato
- [x] 3.2 Fazer `JsonDocumentSummaryStore` e `JsonDocumentTextStore` implementarem as portas de aplicação, preservando o lock de concorrência de `JsonDocumentSummaryStore.salvar`; verificar `test_document_summaries.py` e `test_document_texts.py`

## 4. Apresentação e composition root

- [x] 4.1 Injetar caso de uso e portas no `DocumentTreePanel` removendo imports de `infrastructure` e carregando o seam do lote (`persistir_no_lote`/`gerar_e_persistir`/`refletir_resumo`) sem perder a gravação imediata; verificar que os módulos de documentos não constam mais na allowlist
- [x] 4.2 Atualizar `app_wiring.py` e `chat/documentos.py` para fornecer os adaptadores; verificar o painel com fakes e `make test` verde
- [x] 4.3 Atualizar o protocolo `_PainelDocumentos` de `resumos_job.py` para incluir `persistir_no_lote`/`gerar_e_persistir` e relocar o gancho `_gerar_resumo`; verificar o lote de documentos gravando no worker

## 5. Testes e allowlist

- [x] 5.1 Migrar os testes puros de documentos para `tests/test_domain`/`tests/test_application` e deixar no painel apenas wiring, estado e thread; verificar contagem e ausência de `DISPLAY` nos testes puros
- [x] 5.2 Remover as 8 entradas de documentos da allowlist; verificar `tests/architecture` verde sem entradas obsoletas
- [x] 5.3 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento
