## 1. Shard e wrapper de notícias

- [x] 1.1 Implementar a derivação do shard `NOTICIAS-<ANO>-<MES>` a partir da chave estável (`noticias/<ANO>/<MES>/...`), com fallback para chave fora do padrão; verificar com teste os nomes e o fallback
- [x] 1.2 Implementar o wrapper de notícias que mapeia `(NOTICIAS, chave)` para o shard e delega `obter`/`salvar` aos stores JSON, mesclando os shards em `resumos`; verificar round-trip e mesclagem de resumos

## 2. Wiring

- [x] 2.1 Usar o wrapper na construção dos stores de notícias (`NoticiasCatalog`/`NoticiasPanel`); verificar que Documentos continua com os stores concretos e que o chat (que usa o escopo `NOTICIAS`) segue funcionando sem mudanças

## 3. Migração

- [x] 3.1 Migrar `document-texts/NOTICIAS.json` e `document-summaries/NOTICIAS.json` para os shards, parseando ano e mês da chave, sem reconverter e sem tocar os `<TICKER>.json` de Documentos; verificar migração, idempotência e não interferência

## 4. Escala

- [x] 4.1 Cobrir a escala: com N notícias distribuídas em vários meses, a gravação de cada uma toca apenas o shard do seu mês, verificado por contagem de arquivos lidos/gravados

## 5. Quality Gate

- [x] 5.1 Executar `make lint` e `make complexity` sem erros
- [x] 5.2 Executar `pytest -m "not llm"` sem regressões
- [x] 5.3 Executar `openspec validate noticias-cache-sharding`

## 6. Documentação

- [x] 6.1 Atualizar `README.md`/`panels.md` se descreverem o cache de texto/resumo das notícias
