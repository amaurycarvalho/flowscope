## 1. Núcleo de hash e registro

- [x] 1.1 Criar helper compartilhado de hash SHA-256 do conteúdo bruto em `infrastructure` e verificar com teste unitário de digest conhecido
- [x] 1.2 Definir a porta `HashRegistryStore` em `application` (consultar/registrar/remover por escopo) e verificar com um duplo de teste
- [x] 1.3 Implementar `JsonHashStore` em `infrastructure` (um por ticker para documentos, um global para notícias) com gravação atômica e lock, e verificar com testes de round-trip, arquivo ausente e corrompido
- [x] 1.4 Implementar a política pura de decisão de deduplicação (manter/descartar com validação do canônico) e verificar com testes de tabela cobrindo hash novo, duplicata e canônico inexistente
- [x] 1.5 Implementar a guarda de conteúdo (vazio, só espaços, abaixo do piso configurável de 1 KB) e verificar com testes de borda

## 2. Remoção e poda dos derivados

- [x] 2.1 Adicionar remoção de entrada aos stores de texto e resumo de documentos e verificar que os demais itens permanecem
- [x] 2.2 Adicionar remoção de entrada nos shards de texto e resumo de notícias, traduzindo o escopo para `NOTICIAS-<ANO>-<MES>`, e verificar que a remoção toca apenas o shard do item
- [x] 2.3 Adicionar remoção de entrada ao `NoticiasIndexStore` e verificar que os marcadores da "Geral" são preservados
- [x] 2.4 Implementar a remoção do arquivo nas raízes de documentos e no cache de notícias e a poda combinada (arquivo + resumo + texto + índice) e verificar que a remoção não afeta outros itens

## 3. Hooks de download

- [x] 3.1 Integrar a deduplicação em `DocumentosRelevantesProvider.persistir` e verificar que uma duplicata exata não é gravada nem registrada
- [x] 3.2 Integrar a deduplicação em `AquisicaoDocumentos._persistir_material_fact` e verificar o descarte de duplicata de material fact
- [x] 3.3 Integrar a deduplicação em `InformeMensalArquivoProvider.persistir` e verificar o descarte de duplicata de informe
- [x] 3.4 Integrar a deduplicação em `BdrDividendProvider._obter_pdf`, garantindo que a duplicata não é gravada mas os bytes continuam retornando para a extração, e verificar com teste do fallback de dividendo
- [x] 3.5 Integrar a deduplicação em `AquisicaoNoticias._persistir` e verificar que a duplicata não é gravada nem indexada, sem remover entradas de outros itens

## 4. Housekeeping no "Atualizar"

- [x] 4.1 Implementar o caso de uso de housekeeping de documentos por ticker (enumeração das três raízes, ordem cronológica, hash, decisão) e verificar com teste de duplicatas legadas mantendo o mais antigo
- [x] 4.2 Implementar o caso de uso de housekeeping de notícias global (dirigido pelo índice, ordem cronológica) e verificar com teste de duplicatas legadas entre datas/URLs diferentes
- [x] 4.3 Integrar o housekeeping de documentos ao fluxo de "Atualizar" da sub-aba "Documentos" em background, antes da remontagem, e verificar com teste de `app_actions`
- [x] 4.4 Integrar o housekeeping de notícias ao fluxo de "Atualizar" da sub-aba "Notícias" em background, antes da remontagem, e verificar com teste de `noticias_actions`
- [x] 4.5 Garantir cancelamento e tolerância a falhas isoladas no housekeeping e verificar com teste de falha por arquivo sem interrupção do restante

## 5. Testes e verificação

- [x] 5.1 Cobrir a integração do registro compartilhado entre as raízes de documentos do mesmo ticker e a ausência de dedup entre tickers distintos
- [x] 5.2 Cobrir a dedup global de notícias entre categorias de topo diferentes
- [x] 5.3 Rodar a suíte de testes completa e garantir que os testes de fronteira de camadas (`tests/architecture`) continuam passando
- [x] 5.4 Rodar lint e complexity sem erros
- [x] 5.5 Executar `openspec validate deduplicacao-por-hash` e confirmar o change válido
