## Context

Ver `proposal.md` — Why. A resolução de tickers de FII depende de `GetListFunds` (lista completa por tipo) e `GetListClassFund` (identidade/CNPJ da classe). A API da B3 responde de forma intermitente com páginas vazias e corpos vazios, e o cache atual grava listas parciais por 30 dias. O código relevante está em `infrastructure/b3/funds_client/` e `infrastructure/b3/fund_repository.py`.

## Goals / Non-Goals

**Goals:**
- Garantir que a listagem de fundos usada na resolução seja completa antes de ser cacheada.
- Distinguir “B3 indisponível/listagem incompleta” de “ticker não existe na B3”.
- Persistir ticker → `idFNET` → CNPJ e usar essa identidade como fallback em falhas futuras.
- Manter o contrato tolerante de `listar_fundos` para chamadores existentes.

**Non-Goals:**
- Não alterar o contrato externo da B3 nem introduzir dependências novas.
- Não mudar a prioridade de fontes fundamentalistas (Fundamentus → B3 → CVM Anual → Papel).
- Não persistir resultados negativos.
- Não migrar nem reescrever as specs legadas de resolução além do delta necessário.

## Decisions

### 1. Resultado de listagem explícito (`ListagemFundos`)

Introduzir um resultado interno com `fundos`, `completa` e `total_records`. `obter_listagem(type_fund)` é a API que sabe se a coleta foi completa; `listar_fundos` continua devolvendo apenas a lista (vazia em falha) para não quebrar chamadores existentes.

- **Alternativa descartada**: lançar exceção em `listar_fundos`. Quebraria chamadores tolerantes e a distinção ficaria implícita no tipo da exceção.

### 2. Paginação resiliente e cache íntegro

- Usar `pageSize=120` (maior valor aceito; acima disso a API devolve lista vazia).
- Validar cada página com `executar_com_retry` + `validar`: página vazia é inválida quando `pageNumber <= totalPages` já conhecido. O validador consome o orçamento de tentativas e aplica backoff.
- Só gravar cache quando `len(coletados) == totalRecords`; em coleta parcial, preservar a última listagem completa em cache e retornar `completa=False`.
- Versionar as chaves com `_chave_cache`: `fundos_listados` (já inclui `PARSER_VERSION`) e `fund_resolution`. As chaves legadas `fundos_listados_{tipo}` e `fund_resolution_{ticker}` deixam de ser lidas, descartando listas parciais existentes sem migração manual.

- **Alternativa descartada**: aumentar apenas o TTL/retry HTTP. Não resolve página vazia com HTTP 200 nem o cache parcial.

### 3. Retry de corpo vazio no `GetListClassFund`

Mover o parse JSON para dentro do motor de retry em `_get_json`: falhas de decodificação passam a ser convertidas em `requests.RequestException` e repetidas pela política central. Um parâmetro opcional `validar` permite rejeitar semanticamente respostas vazias (página de listagem). Isso cobre o passo 5 sem criar um segundo mecanismo de retry.

- **Alternativa descartada**: `try/except JSONDecodeError` local no `GetListClassFund`. Duplicaria backoff e não cobriria a validação semântica de páginas.

### 4. Store persistente de identidade por ticker

Novo `JsonFundIdentityStore` em `infrastructure/b3/fund_identity_store.py`:

- Arquivo por ticker em `<cache>/fund_identity/<TICKER>.json` (mesmo padrão de `guidance/` e `fundamentos/`), evitando contenção de escrita num índice único.
- Conteúdo: `schema_version`, `ticker`, `id_fnet`, `primary_id`, `name`, `trading_name`, `cnpj`, `type_fund`, `updated_at`.
- Escrita atômica (reutiliza `_atomic_write_bytes`), leitura tolerante a ausência/corrupção/versão antiga, sem expiração (CNPJ muda raramente).
- Nunca grava resultado negativo.

- **Alternativa descartada**: índice único `fund_identity.json`. Mais simples de ler, porém sujeito a lost update e corrupção total do mapa.

### 5. Semântica de fallback no `B3FundRepository`

`find_by_ticker` passa a:

1. Obter a listagem via `obter_listagem` para cada tipo.
2. Se a listagem for **completa** e o ticker não existir → retornar `None` (não usa cache antigo; evita mascarar fundo removido).
3. Se a listagem estiver **incompleta** ou a B3 falhar → ler o store persistente; se houver identidade, reconstruir `B3Fund` a partir dela.
4. Se `GetListClassFund` falhar após encontrar o primário → também usar o store.
5. Em resolução bem-sucedida, gravar/atualizar o store.

- **Alternativa descartada**: consultar o store antes da B3. Serviria dados velhos mesmo com a fonte saudável e impediria atualização do CNPJ.

### 6. Injeção e compartilhamento

`Nucleo` cria um `JsonFundIdentityStore` no diretório de cache e injeta em `B3FundRepository`. Para que o fallback CVM Anual use a mesma identidade/cache, `CvmAnnualFundDataProvider` e `CvmIndexadoresProvider` passam a receber um resolver que delega ao `B3FundRepository` compartilhado, em vez de instanciar um repositório padrão isolado.

### 7. Testes

Cobrir, no nível de cliente/repositório: página vazia intermitente repetida; lista parcial não sobrescreve cache completo; chave versionada ignora cache legado; corpo vazio do `GetListClassFund` repetido; store grava identidade, serve fallback em falha, ignora corrupção/versão antiga e não grava negativos. No nível de aplicação: CNPJ fiscal preenchido via fallback persistido quando a B3 falha. Verificação padrão da change: `make lint`, `make complexity` e os testes impactados.

## Risks / Trade-offs

- **CNPJ antigo para fundo removido** → a listagem completa prevalece e não consulta o store; o fallback só atua em indisponibilidade/incompletude.
- **API da B3 mudar o limite de `pageSize`** → a validação de coleta completa falha de forma explícita (lista não é cacheada) e o teste de contrato detecta.
- **Crescimento do cache por ticker** → um arquivo JSON pequeno por ticker; custo desprezível e auditável.
- **Duplicação de retries (HTTP interno + parse externo)** → aceitável; o retry externo só atua em falha de conteúdo, mantendo a política central num único ponto.
- **Store por ticker não é transacional entre processos** → a aplicação é single-process; a escrita atômica evita arquivo corrompido.

## Migration Plan

1. Publicar o código com a nova chave versionada; listas parciais antigas deixam de ser lidas automaticamente.
2. Na primeira resolução bem-sucedida de cada ticker, o store persistente é criado.
3. Rollback: remover o uso do store e voltar a chave de listagem anterior; os arquivos de identidade permanecem inertes e podem ser apagados.

## Open Questions

Nenhuma.
