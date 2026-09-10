## Context

Ver `proposal.md - Why`. Estado atual relevante:

- `B3FundosClient` já usa `CacheManager.get_or_fetch` para a lista de fundos (30d), a resolução de ticker (30d), a listagem de documentos (1d), codeCVM/cadastro (30d), fatos relevantes/notícias (1d) e páginas estáticas (7d).
- `buscar_html_documento` (`funds_client.py`) faz `_requisicao_get` direto, sem cache. É chamado por `FundosRepository.extrair_detalhes` (proventos `type=41`) e por `B3ReportsRepository.extrair_informe` (`type=40`).
- `listar_candidatos` (`GetListClassFund`) faz `_get_json` direto, sem cache; é o caminho de `B3FundRepository.find_by_ticker` (`selecionar_candidato`), usado por `B3FundamentalRepository` e por `resolver_identidade` (CVM). O `resolver_ticker` tem cache, mas `find_by_ticker` não o utiliza.
- O `id` de documento FundosNet é imutável (retificações geram novo documento/`id`); a identidade `ticker → idFNET` muda raramente.
- Existe `ConditionalCache` (com `parser_version` e validadores HTTP) e o `CacheManager` simples; o cliente B3 hoje usa apenas o segundo.

## Goals / Non-Goals

**Goals:**
- Eliminar o rebaixamento repetido de documentos e a reconsulta de identidade entre execuções.
- Manter a aquisição tolerante: em falha de rede, servir o que já está em cache.
- Uniformizar TTLs/nomes de chave e versioná-los pela versão do parser.

**Non-Goals:**
- Não alterar parsing, contratos de porta ou o fluxo de listagem de documentos.
- Não introduzir revalidação HTTP para documentos imutáveis.
- Não mexer no cache do Fundamentus nem nos arquivos anuais da CVM.

## Decisions

### 1. Cache do HTML de documento com `get_or_fetch` e chave versionada

`buscar_html_documento` passa a usar `CacheManager.get_or_fetch` com payload `{"html": ...}`, chave `fund_doc_html_{PARSER_VERSION}_{id_documento}` e TTL longo (ex.: 30 dias). Como o `id` é imutável, não há revalidação remota; o TTL longo e a retenção do próprio cache cobrem a evolução do dado. Em falha de rede, se houver registro, ele é servido; sem registro, a exceção de `_requisicao_get` propaga como indisponibilidade.

Alternativas: `ConditionalCache.get_file_or_revalidate` com ETag/Last-Modified (mais robusto, porém desnecessário para conteúdo imutável e exigiria guardar arquivo + metadados); cachear no nível de `FundosRepository`/`B3ReportsRepository` (duplicaria a lógica em dois pontos). Escolhido o cache no cliente, que já concentra o transporte.

### 2. Cache da identidade com `get_or_fetch`, sem congelar ausência

`listar_candidatos` passa a usar `get_or_fetch` com chave `fund_classes_{PARSER_VERSION}_{id_primario}` e TTL de 30 dias (mesma política de `resolver_ticker`). Se a resposta vier vazia, o registro é invalidado e a lista vazia retornada, para não congelar falhas transitórias nem tickers sem correspondência.

Alternativas: fazer `find_by_ticker` reutilizar `resolver_ticker` (só devolve o `id`, mas `find_by_ticker` precisa de `fundName`/`tradingName`); cachear por ticker (a identidade primária é por fundo, não por ticker). Escolhido cachear a resposta bruta por `id` primário.

### 3. Políticas centralizadas e versão única

Adicionar ao `funds_client.py` uma constante de versão do parser/aquisição e constantes nomeadas para cada TTL, e um helper que monta a chave versionada. Os métodos passam a referenciar essas constantes em vez de literais, atendendo ao item de consistência.

Alternativa: manter literais nos métodos (estado atual), que dificulta a evolução das políticas. Escolhido centralizar.

### 4. Testes de cache com sessão simulada

Reutilizar o padrão de `responses`/`_FakeSession` já presente nos testes de `structured_b3.py` para afirmar que a segunda chamada não dispara HTTP (documento e identidade), que a versão do parser invalida e que falha de rede com cache serve o conteúdo.

## Risks / Trade-offs

- **[Risco] Crescimento do cache em disco com HTML de documentos** → TTL de 30 dias e retenção do `CacheManager`; documentos são pequenos (~6 KB).
- **[Risco] Identidade desatualizada por 30 dias** → mesma política já usada por `resolver_ticker`; a resolução com `idMain` é estável.
- **[Trade-off] Servir documento em cache quando a B3 está indisponível** → aceitável porque o `id` é imutável e o conteúdo não muda.
- **[Risco] Chave versionada invalida cache ao subir a versão** → comportamento desejado; nova versão refaz a aquisição uma vez.

## Migration Plan

1. Adicionar constantes de versão/TTL/chave e o helper de chave no `funds_client.py`.
2. Envolver `buscar_html_documento` no cache.
3. Envolver `listar_candidatos` no cache, invalidando resultado vazio.
4. Adicionar os testes de cache e rodar a suíte.
5. Rollback: remover os invólucros de cache restaura o comportamento anterior; as chaves novas são inertes.

## Open Questions

- Nenhuma pendente que altere specs, abordagem ou tarefas.
