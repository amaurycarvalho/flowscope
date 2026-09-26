## 1. Ordenação dos pendentes

- [x] 1.1 Implementar a ordenação dos pendentes de notícias por grupo (índice em `SECOES_ORDEM`) e, dentro do grupo, por data de publicação decrescente, sem alterar a ordem usada pelos Documentos; verificar com teste que os itens saem na sequência de grupos e datas esperadas
- [x] 1.2 Tratar `data_publicacao` em formatos variados, ausente ou inválida, com fallback `(ano, mes)` do caminho e desempate determinista; verificar com testes dos formatos `"AAAA-MM-DD hh:mm:ss"`, `"AAAA-MM-DD"`, vazio e data empatada

## 2. Persistência no worker

- [x] 2.1 Ligar o gancho de persistência no worker para o lote de notícias, reutilizando o seam de `documentos-resumo-lote-persistente`; verificar com teste que o resumo é gravado antes do próximo item
- [x] 2.2 Cobrir interrupção: cancelar o lote de notícias após alguns resumos e verificar que todos os já gerados estão no cache persistente

## 3. Integração no lote

- [x] 3.1 Fazer `_resumir_noticias_pendentes` consumir a lista ordenada; verificar com teste de lote com itens em mais de uma seção que a ordem de geração segue `SECOES_ORDEM` e a cronologia decrescente

## 4. Quality Gate

- [x] 4.1 Executar `make lint` e `make complexity` sem erros
- [x] 4.2 Executar `pytest -m "not llm"` sem regressões
- [x] 4.3 Executar `openspec validate noticias-resumo-lote-ordenado`

## 5. Documentação

- [x] 5.1 Atualizar `panels.md`/`README.md` se a ordem do lote de notícias for descrita neles
