## 1. Store segura a concorrência

- [x] 1.1 Proteger o *read-modify-write* de `JsonDocumentSummaryStore.salvar` com um lock, preservando os resumos já gravados; verificar com teste de duas escritas concorrentes de chaves diferentes em que ambas permanecem no arquivo
- [x] 1.2 Verificar que a gravação atômica (temp + rename) e a tolerância a arquivo corrompido continuam cobertas pelos testes existentes da store

## 2. Persistência no worker

- [x] 2.1 Introduzir na fachada do painel um método de "gerar e persistir" executável na thread de trabalho, que grava no store e devolve o `DocumentoArquivo` atualizado sem tocar em widgets nem nos mapas de memória; verificar com teste que a store recebe o resumo ao chamá-lo
- [x] 2.2 Ajustar `ResumosPendentesJob` para, ao gerar cada resumo, persistir antes de processar o próximo item; verificar com teste que, ao publicar o `RESULTADO` de um item, o resumo já está no store
- [x] 2.3 Ajustar a aplicação do resultado na thread do Tk para apenas refletir em memória e pré-visualização, sem regravar; verificar com teste que a aplicação não chama o store

## 3. Lote de Documentos

- [x] 3.1 Ativar o caminho de persistência no worker no `DocumentTreePanel`; verificar que os testes de lote existentes continuam passando
- [x] 3.2 Cobrir interrupção: cancelar o lote após alguns resumos e verificar que todos os já gerados estão no cache persistente

## 4. Quality Gate

- [x] 4.1 Executar `make lint` e `make complexity` sem erros
- [x] 4.2 Executar `pytest -m "not llm"` sem regressões
- [x] 4.3 Executar `openspec validate documentos-resumo-lote-persistente`

## 5. Documentação

- [x] 5.1 Atualizar `README.md`/`panels.md` se o comportamento observável do lote de documentos for descrito neles
