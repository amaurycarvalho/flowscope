## Why

O cache atual é puramente baseado em TTL ou em existência de arquivo, o que não é um bom proxy de "frescor". O provider do Fundamentus (`fundamentus-fundamental-provider`) guarda o HTML por 7 dias sem qualquer validação de conteúdo, e os downloaders anuais da CVM (`cvm-monthly-fund-data`) reutilizam o ZIP local para sempre. Como a CVM atualiza o ZIP do ano corrente ao longo do ano (novos meses e reapresentações), o dado do ano corrente fica permanentemente desatualizado — um bug real de frescura, não uma mera otimização. Além disso, o projeto tem três fontes com necessidades de revalidação distintas (data de cotação, validadores HTTP, hash), hoje tratadas de forma ad-hoc.

## What Changes

- Introduzir uma abstração genérica de **cache condicional** que separa *frescor* (quando o valor é considerado válido), *revalidação* (checagem barata contra a fonte remota) e *retenção* (quando evictar do disco), com protocolo de `Validator` plugável.
- Adicionar validadores concretos: `DateValidator` (campo `Data últ cot`) e `HttpValidator` (`ETag`/`Last-Modified`, `304`), com chaves versionadas por `parser_version`/`SOURCE_SCHEMA_VERSION`, escrita atômica e coalescência de checagens de rede.
- Aplicar ao provider do Fundamentus: revalidar o snapshot por `Data últ cot` (primário) e validadores HTTP (secundário), cachear HTML cru com versão do parser e devolver o resultado do cache (hit/revalidado/atualizado) para a camada de apresentação.
- **Corrigir o bug da CVM**: revalidar o arquivo anual contra a fonte remota (validador HTTP) antes de reutilizar o ZIP local, rebaixando apenas quando a fonte mudou; em falha de revalidação, servir o arquivo local (stale-on-failure) e atualizar os metadados.
- Propagar o resultado do cache até a statusbar para exibir "Dados atualizados" quando houver atualização real, sem acoplar infraestrutura à GUI.

## Capabilities

### New Capabilities

- `conditional-data-cache`: Mecanismo genérico de cache condicional com validadores plugáveis, separação de políticas de frescor/retenção/revalidação, chaves versionadas, escrita atômica e reporte de resultado de cache.

### Modified Capabilities

- `fundamentus-fundamental-provider`: Adiciona revalidação condicional do snapshot por `Data últ cot` e validadores HTTP, cache de HTML cru versionado e reporte do resultado de cache.
- `cvm-monthly-fund-data`: Adiciona revalidação remota do arquivo anual antes de reutilizar o ZIP local e comportamento stale-on-failure, corrigindo a frescura do ano corrente.

> Nota de ordenação: `fundamentus-fundamental-provider` e `cvm-monthly-fund-data` ainda não foram arquivadas para `openspec/specs/` (changes completas porém não arquivadas). Os deltas usam `## ADDED Requirements`; arquivar/ sincronizar essas capabilities antes desta change garante que as novas requirements sejam anexadas às specs existentes em vez de criar specs incompletas.

## Impact

- **Código afetado**: `src/flowscope/infrastructure/cache.py` (novo cache condicional e validadores), `src/flowscope/infrastructure/fii/fundamentus/provider.py` e `client.py` (captura de `ETag`/`Last-Modified` e revalidação), `src/flowscope/infrastructure/cvm/datasets.py` e `downloader.py` (revalidação do ZIP anual), `src/flowscope/presentation/gui/` (mensagem "Dados atualizados").
- **Dados**: cache em `~/.cache/flowscope/` com metadados de revalidação (`etag`, `last_modified`, `fetched_at`, `parser_version`).
- **Dependências**: nenhuma nova dependência externa; reaproveita `requests` e o `CacheManager` existente.
- **Compatibilidade**: API pública dos providers preservada (`get(ticker)`); `force_refresh`/invalidação adicionados como opção explícita.
