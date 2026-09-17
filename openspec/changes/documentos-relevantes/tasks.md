## 1. Pré-requisito

- [x] 1.1 Verificar que a infraestrutura base está implementada (`B3FundosClient`, `CacheManager`, resolução de ticker)
- [x] 1.2 Confirmar que a leitura da árvore será consumida pela change `visualizacao-documentos` e que a extração de texto ficará fora desta change

## 2. Domínio — Entidade e categorias

- [x] 2.1 Implementar `DocumentoRelevante` dataclass com metadados (sem `texto_extraido` e sem `to_text()`)
- [x] 2.2 Implementar o mapeamento de categorias (`{1: "Fato Relevante", 2: "Assembleia", 3: "Comunicado ao Mercado", 7: "Relatorio"}`) e o slug de pasta correspondente
- [x] 2.3 Atualizar o `__init__` do domínio de documentos

## 3. Testes do Domínio

- [x] 3.1 Testar criação de `DocumentoRelevante` e acesso aos metadados
- [x] 3.2 Testar o mapeamento de categoria (nome e slug) para todos os códigos

## 4. Infraestrutura — B3FundosClient

- [x] 4.1 Implementar `listar_documentos_relevantes(id_fnet, data_inicio, data_fim, category)` — `GetReportsRelevants`, token com `category`, paginação, cache TTL 1 dia
- [x] 4.2 Tratar `id_fnet=None` retornando lista vazia
- [x] 4.3 Implementar o download do PDF via `exibirDocumento?id=`, com validação `%PDF`
- [x] 4.4 Implementar o cache em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`, sem TTL, com reuso em cache hit
- [x] 4.5 Implementar a listagem consolidada das 4 categorias, logando `logger.warning` em falhas por categoria

## 5. Leitura da árvore

- [x] 5.1 Expor listagem dos documentos em cache de um ticker, com caminho e categoria, ordenados do mais recente ao mais antigo
- [x] 5.2 Retornar lista vazia para ticker sem cache, sem erro

## 6. Testes da Infraestrutura

- [x] 6.1 Testar `listar_documentos_relevantes` com mock de HTTP (fixture JSON de resposta)
- [x] 6.2 Testar `listar_documentos_relevantes` com `id_fnet=None`
- [x] 6.3 Testar download com PDF válido, conteúdo não-PDF e cache hit
- [x] 6.4 Testar a iteração pelas 4 categorias com falha isolada
- [x] 6.5 Testar a leitura ordenada e o ticker sem documentos

## 7. Quality Gate

- [x] 7.1 Executar `make lint` e corrigir avisos/erros
- [x] 7.2 Executar `make test` e garantir que todos os testes passam
- [x] 7.3 Executar `openspec validate documentos-relevantes` e garantir que a change permanece válida
