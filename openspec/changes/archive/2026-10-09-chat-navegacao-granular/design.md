## Context

Ver `proposal.md` — Why. Hoje `application/chat/documentos.py` monta `/documentos/<ticker>` com três folhas agregadas (`curto`/`longo`/`texto`), nas quais `curto`/`longo` são a junção dos resumos de todos os documentos e `texto` é a concatenação truncada em `TETO_DOCUMENTO` (12.000 chars) na ordem ano/mês/categoria decrescente. `application/chat/guidance.py` expande `/guidance/<ticker>/<ano>/<mes>/<guidance>` sem índice. O manifesto (`application/chat/manifesto.py`) descreve o mapa canônico e as listas de chaves; o protocolo serializa só o bloco de resultados (`application/chat/protocolo.py`), e o loop vive em `application/chat/consultar.py`, que reusa a navegação entre perguntas. `/noticias` (`application/chat/noticias.py`) já é o modelo desejado: índice compacto por grupo + nó por item com `titulo`/`resumo`/`texto`.

Restrições: a árvore é estritamente cache-only e determinística; o manifesto é prefixo cacheável com teto de 4.000 tokens; e o chat é lido como JSON determinístico, sem timestamps. As changes `chat-navegacao-robusta` e `documentos-arvore-ramos` já estão aplicadas no código (manifesto dinâmico, ramos `/guidance` e `/direitos-obrigacoes`) mas não arquivadas; as deltas desta change pressupõem aquele texto.

## Goals / Non-Goals

**Goals:**
- Dar granularidade por documento e um índice por ticker, para a LLM escolher "o mais recente" e ler o `texto` do alvo sem truncamento cruzado.
- Expor índice de guidance por ticker e metadados estruturados (categoria, período, nome) navegáveis e pesquisáveis.
- Manter um `foco` entre turnos para anáforas e um playbook de intenção→ramo.
- Tornar abas/sub-abas descobríveis e impedir conteúdo pesado no manifesto.

**Non-Goals:**
- Não introduzir índice vetorial nem alterar `buscar_semantico`.
- Não paginar textos integrais (`obter` com `offset/limite`) — fica para change futura; o teto por texto permanece.
- Não alterar o formato de cache, os stores de resumo/texto nem a persistência.
- Não mexer nos ramos de fundamentos/notícias/direitos além de reutilizar o padrão de índice.

## Decisions

### 1. `/documentos` passa a espelhar `/noticias`: índice + nó por documento

`_construir_ticker` passa a montar `/documentos/<ticker>/indice` e, para cada documento recuperável, `/documentos/<ticker>/<chave>` com filhos `curto`, `longo`, `texto`. As folhas agregadas por ticker são removidas. Alternativa: manter agregados e só adicionar o índice — rejeitada porque o `longo` agregado (dezenas de milhares de chars) foi justamente o que fez a LLM parar antes do documento-alvo; mantê-lo perpetua o comportamento.

### 2. `texto` é do documento, não do ticker

O `carregar` de cada nó lê `texto_store.textos(ticker)` uma vez (mapa por chave) e devolve o texto daquele documento, truncado por `TETO_DOCUMENTO`. Como o mapa é lido uma única vez por construção do ramo, o custo é O(n) leituras por ticker, igual ao atual. Alternativa: manter um `texto` por ticker — rejeitada por truncar cruzado entre documentos.

### 3. Chave curta e estável por documento

Reutiliza-se `chave_documento(caminho, base)` (caminho relativo) e uma chave curta derivada por hash (mesmo padrão de `chave_curta_guidance`), para evitar espaços/acentos nos caminhos e manter o nó estável entre construções. Alternativa: usar o nome do arquivo — rejeitada por colidir entre categorias/anos.

### 4. Metadados estruturados no `metadado` e em `campos`

O nó do documento recebe `metadado` legível (`<categoria> — <mmm/aa> — <nome>`) e `campos={"categoria","periodo","nome"}`. O `indice` é uma folha com uma linha por documento, ordenada por (ano, mês, nome) decrescente, com teto de caracteres e `campos={"indice","categoria","periodo","nome"}`. Assim "mais recente" e "qual período" são resolvidos por `listar`/`obter`/`buscar` sem ler o texto.

### 5. Índice de guidance reutilizando a agregação existente

`FonteGuidance` ganha `/guidance/<ticker>/indice`, montado a partir de `agrupar_entradas` e `rotulo_relatorio_gerencial` já existentes, em ordem decrescente, uma linha por entrada (`<mmm/aa>: <guidance> — <rótulo>`). As folhas por mês permanecem e recebem `campos` com período, guidance e relatório. Alternativa: só as folhas — rejeitada porque a evolução temporal exigiria `obter` de cada mês.

### 6. Foco entre turnos calculado no caso de uso

O `foco` é o caminho do último `obter` bem-sucedido. Como `ProtocoloNavegacao` é stateless por turno, o `ConsultarChatUseCase` inspeciona os resultados do ciclo, atualiza `estado.foco` e o repassa à serialização; `resetar_navegacao` e a mudança de assinatura zeram o foco junto da navegação. Alternativa: reusar só o histórico textual — rejeitada por depender de heurística do modelo para mapear "nesse RG".

### 7. Playbook no manifesto e no prompt

O manifesto recebe um playbook dinâmico de intenção→ramo (guidance via índice; RG mensal identificado pelo índice de guidance; comentar um documento via `texto` integral; resumo/lista de vários via `curto`/`longo`; app via `/flowscope/abas`/`meta`) e o `SYSTEM_PROMPT` reforça "comentar documento → texto integral; resumir vários → resumos". As folhas de documento levam `metadado` legível para que `listar` distinga resumo de texto integral. A categoria de cache (`Relatorio`) não distingue um RG mensal de cartas/comunicados; por isso o playbook orienta confirmar o alvo pelo conteúdo e usar o índice de guidance como fonte autoritativa dos RGs. Alternativa: confiar no mapa de caminhos — rejeitada porque a LLM parou nos resumos agregados e, ao ser corrigida para os resumos, deixou de abrir o texto integral do documento.

### 8. Manifesto: aba navegável, sub-abas listadas e teto de metadado

`_caminhos_flowscope` passa a incluir `/flowscope/abas/<aba>`; uma seção de listas passa a nomear as sub-abas por aba; e `_metadados` ignora metadados acima de um teto curto (ex.: 120 chars), evitando que o texto integral das sub-abas entre no manifesto e derrube a seção inteira por estouro de tokens. Alternativa: manter como está — rejeitada porque hoje o manifesto degrada para "só chaves" e perde metadados curtos úteis.

### 9. Índice autoexplicativo: trecho do resumo, tipo e duplicados

Cada linha do `/documentos/<ticker>/indice` passa a embutir um trecho curto do resumo (corte em fim de frase/palavra) e o tipo `RG mensal`/`documento`, sendo `RG mensal` derivado do ledger de guidance via um resolvedor opcional `rg_chaves` injetado em `FonteDocumentos` (no `chat_panel`). Documentos repetidos no mesmo mês/categoria recebem `posição/total`. Alternativa: manter o índice só com metadados — rejeitada porque a categoria de cache (`Relatorio`) não distingue um RG de cartas/comunicados, e a LLM gastava vários turnos reinvestigando (ex.: set/26 vs ago/26).

### 10. Anti-procrastinação e reuso do foco

O `PROTOCOLO` e o `SYSTEM_PROMPT` passam a proibir promessas de navegação ("vou abrir"): se faltam dados, a LLM emite `solicitacoes` com `resposta` nulo e só finaliza com o conteúdo já no contexto, reusando o `foco`. Alternativa: confiar na disciplina do modelo — rejeitada porque a sequência observada terminou turnos com "vou abrir…" e exigiu um "faça" do usuário.

## Risks / Trade-offs

- **[Risco] Manifesto cresce com o índice e as listas de sub-abas** → o `indice` é conteúdo de nó (não manifesto); as listas de sub-abas são curtas; o teto de 4.000 tokens e a degradação para "só chaves" continuam valendo, com teste de regressão.
- **[Risco] Mais nós por ticker aumentam a construção da árvore** → leitura de resumo/texto continua uma vez por ticker no `FonteDocumentos`; sem I/O extra por nó.
- **[Risco] Remoção das folhas agregadas quebra consumidores** → apenas o chat consome `/documentos`; o ramo da sub-aba Documentos é independente. Mitigado por testes de árvore e de manifesto.
- **[Trade-off] `foco` é estado implícito da sessão** → torna-se explícito no bloco do turno, reusando a cota de navegação; é determinístico e some com `resetar_navegacao`/mudança de assinatura.
- **[Risco] Conflito com as changes pendentes** (mesmas capabilities) → as deltas desta change incluem o texto de `chat-navegacao-robusta`/`documentos-arvore-ramos`; arquivá-las antes desta mantém os specs coerentes.

## Migration Plan

Sem migração de dados. Rollback = restaurar as folhas agregadas por ticker, remover os índices, o `foco` e o playbook. Conviver com as changes pendentes arquivando-as primeiro.

## Open Questions

- Paginação de `texto` integral (`obter` com `offset/limite`) para "o que mais há de relevante" em documentos longos — deferida; o `texto` do documento-alvo já destrava as perguntas do exemplo dentro do teto atual.
