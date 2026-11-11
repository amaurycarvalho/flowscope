## Why

Os dados fiscais (CNPJ, administrador e gestor) dos FIIs da watchlist ficam vazios porque a resolução ticker → fundo B3 falha para a maior parte dos FIIs: a paginação de `GetListFunds` é interrompida por páginas vazias intermitentes, o resultado parcial é cacheado por 30 dias e, sem identidade B3, tanto o provedor B3 quanto o fallback CVM Anual ficam inutilizados. Na máquina investigada, apenas 40 de 530 FIIs estavam no cache e só `ALZR11` (único da watchlist presente no subconjunto) exibia dados fiscais. Release alvo: 1.8.1.

## What Changes

- Tornar a listagem de fundos da B3 completa e resistente a respostas vazias intermitentes: `pageSize=120` (máximo aceito), repetição de páginas vazias com backoff e só cachear a lista quando `len(results) == totalRecords`.
- Preservar a última listagem completa em caso de atualização parcial/indisponível, em vez de sobrescrever o cache com uma lista truncada.
- Invalidar as chaves de cache legadas de listagem e de resolução (versionar as chaves) para descartar listas parciais e ausências já gravadas.
- Tratar corpo vazio intermitente do `GetListClassFund` como conteúdo inválido repetível, usando o validador do motor de retry central.
- Adicionar cache persistente ticker → `idFNET` → CNPJ (com nome do fundo e tipo), escrito a cada resolução bem-sucedida e consultado como fallback quando a B3 estiver indisponível ou a listagem vier incompleta.
- Não persistir resultados negativos (ticker sem correspondência) para não congelar falhas transitórias.
- Garantir que a identidade persistida esteja versionada, com escrita atômica e tolerância a corrupção, e que o CNPJ alimente o fallback CVM Anual mesmo quando a B3 falhar.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `b3-fii-extraction`: a listagem de fundos passa a exigir coleta completa antes de cachear, repetir páginas vazias intermitentes e repetir corpos vazios do `GetListClassFund`; a identidade resolvida é persistida por ticker e reutilizada quando a fonte está indisponível.
- `ticker-resolution`: a resolução ticker → `idFNET` passa a manter um cache persistente ticker → `idFNET` → CNPJ e a usar essa identidade como fallback em falhas da B3, sem cachear resultados negativos.

## Impact

- Infraestrutura B3: `infrastructure/b3/funds_client/constants.py`, `funds_client/fundos.py`, `funds_client/documentos.py` e `funds_client/base.py` (validação de resposta vazia).
- Repositório de identidade: `infrastructure/b3/fund_repository.py` e novo store persistente de identidade (ex.: `infrastructure/b3/fund_identity_store.py`).
- Composição: `presentation/composicao.py` injeta o store no repositório de fundos.
- Cache em disco: novo diretório/chave de identidade por ticker; chaves de listagem versionadas.
- Sem novas dependências; sem mudança de contrato externo da B3.
