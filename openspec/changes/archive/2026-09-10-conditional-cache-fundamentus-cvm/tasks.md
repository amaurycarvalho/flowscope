## 1. Mecanismo genérico de cache condicional

- [x] 1.1 Criar `src/flowscope/infrastructure/conditional_cache.py` com `CacheOutcome`, `CacheRecord`, `RevalidationStatus` e o protocolo `Validator`, verificando com teste unitário de tipos/contrato
- [x] 1.2 Implementar `get_or_revalidate` no mecanismo, com políticas independentes de frescor, `revalidate_after` (coalescência) e retenção, reaproveitando diretório e escrita atômica do `CacheManager`; cobrir hit/revalidado/atualizado/miss em testes
- [x] 1.3 Implementar chave versionada por `parser_version` (registro de versão anterior é tratado como miss) e cobrir com teste dedicado
- [x] 1.4 Implementar `HttpValidator` (`If-None-Match`/`If-Modified-Since`, trata `304` como `UNCHANGED`, `200` como `CHANGED`, falha como `UNKNOWN`) e cobrir com mocks de resposta
- [x] 1.5 Implementar tolerância a registro corrompido/ausente/expirado como miss e escrita `tmp` + `rename`; cobrir com testes de corrupção e atomicidade
- [x] 1.6 Implementar `get_file_or_revalidate` para artefatos em arquivo (ZIP/CSV), com probe remoto e fallback stale-on-failure; cobrir com teste de fonte inalterada, alterada e probe indisponível
- [x] 1.7 Garantir retrocompatibilidade de `CacheManager.get_or_fetch`; rodar `make test` e confirmar que os testes existentes de cache continuam passando

## 2. Fundamentus: revalidação condicional

- [x] 2.1 Adicionar ao `FundamentusClient` um método que devolve `requests.Response` (headers + texto) preservando `fetch` atual; cobrir com teste de headers expostos
- [x] 2.2 Implementar `DateValidator` (extrai `Data últ cot` do HTML remoto; `UNCHANGED` quando não posterior à armazenada) e cobrir com fixtures `PETR3`/`FIIB11`
- [x] 2.3 Migrar `FundamentusProvider` para `get_or_revalidate` com HTML cru versionado por `parser_version`, usando data como validador primário e HTTP como secundário; cobrir data igual, data nova e `304`
- [x] 2.4 Aplicar coalescência e TTL de segurança por ticker; cobrir chamadas repetidas no intervalo e TTL vencido
- [x] 2.5 Expor `get_with_outcome` (valor + `CacheOutcome`) e `force_refresh`, mantendo `get(ticker)`; cobrir atualização forçada e reporte de atualização
- [x] 2.6 Verificar troca de `parser_version` invalida o cache anterior (teste dedicado)

## 3. CVM: corrigir frescura do arquivo anual

- [x] 3.1 Revalidar o arquivo anual em `CvmDatasetDownloader.baixar_ano` via `get_file_or_revalidate` antes de reutilizar o ZIP local; cobrir fonte inalterada (não baixa) e alterada (rebaixa)
- [x] 3.2 Aplicar a mesma revalidação em `CvmMonthlyDownloader.baixar_ano`; cobrir com teste equivalente
- [x] 3.3 Registrar `last_modified`/`etag`/`revalidated_at` nos metadados do ano; cobrir com teste de metadados
- [x] 3.4 Implementar stale-on-failure (probe falha e existe ZIP local ⇒ usa local com aviso); cobrir com mock de exceção de rede
- [x] 3.5 Teste de integração: novo mês publicado no ZIP do ano corrente é refletido após revalidação (fixture de ZIP com e sem o mês)
- [x] 3.6 Rodar `make test` e confirmar que os testes de `cvm-monthly-fund-data` e do motor FFO continuam verdes

## 4. Apresentação: sinalizar atualização

- [x] 4.1 Propagar o `CacheOutcome` do provider até a aplicação e agregar "houve atualização" no `FundamentalAnalysisUseCase`; cobrir com teste de agregação
- [x] 4.2 Exibir "Dados atualizados" na statusbar ao final da carga quando houve atualização; cobrir com teste de apresentação usando o dublê de view
- [x] 4.3 Rodar `make lint` e corrigir eventuais achados do `ruff`

## 5. Validação final

- [x] 5.1 Rodar `make test` com cobertura e garantir o limite de 85% do Makefile
- [x] 5.2 Validar a change com `openspec validate conditional-cache-fundamentus-cvm --strict` e resolver avisos aplicáveis
- [x] 5.3 Confirmar que `fundamentus-fundamental-provider` e `cvm-monthly-fund-data` foram sincronizadas/arquivadas antes do archive desta change (ordenação registrada em design.md)
