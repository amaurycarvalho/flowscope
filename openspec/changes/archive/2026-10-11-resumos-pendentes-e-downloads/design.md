## Context

Ver `proposal.md` — Why. O comportamento atual de "pendência" é derivado apenas do resumo persistido: `documentos_sem_resumo` usa `_resumo_integro` (`presentation/gui/charts/document_flow_mixin.py`) e `pendentes_ordenados` de notícias usa `long_summary is None` (`application/noticias/lote.py`). O text store já distingue ausência definitiva (`SEM_TEXTO` / branco) de "não convertido" (`application/documento-texto-cache`), mas essa informação não entra na decisão de pendência. A pendência de guidance é derivada do ledger (`application/documentos/document_guidance.py`), e a avaliação por IA descarta toda a cascata quando qualquer chamada falha (`application/avaliar_guidance.py`). A aquisição de material facts deriva o caminho da data de referência, que hoje falha para valores com hora (`infrastructure/b3/documentos_aquisicao.py`), e a deduplicação por conteúdo só atua após o download (`application/deduplicacao.py`). A change `deduplicacao-conteudo` estabelece o registro de hash de conteúdo por escopo, reutilizado como referência de layout.

## Goals / Non-Goals

**Goals:**
- Fazer a pendência refletir "há trabalho acionável", separando ausência definitiva de texto de "não processado".
- Impedir que uma falha persistente de IA mantenha o botão habilitado indefinidamente.
- Estabilizar a identidade de material facts (data interpretada) e evitar re-download por URL já concluída.
- Alinhar a regeneração de resumos truncados em Notícias ao comportamento de Documentos.

**Non-Goals:**
- Não redesenhar a árvore nem a pré-visualização.
- Não alterar o contrato de `ResumoDocumento` nem os tetos de caracteres.
- Não buscar/processar novamente todo o cache de notícias de uma vez (a regeneração ocorre no lote acionado pelo usuário).

## Decisions

### 1. Pendência derivada de um estado "sem texto" pré-computado no worker

Reusar o padrão de `_guidance_pendentes`: o worker que lê o catálogo resolve, numa passada, o conjunto de caminhos com ausência definitiva de texto (lendo o text store e aplicando `tem_texto` sobre o valor persistido — marcador ou branco) e o entrega à thread do Tk, que filtra `documentos_sem_resumo`/`pendentes_ordenados` sem tocar em I/O. Alternativas: (a) consultar o text store no predicado — faz I/O na thread do Tk a cada reavaliação do botão; (b) usar apenas o memo de sessão — incompleto, pois não cobre documentos nunca abertos.

### 2. Serviço de resumo compartilhado para a decisão de pendência

Extrair a decisão "necessita de resumo" (resumo ausente/não íntegro E texto não conclusivamente ausente) para o serviço de aplicação já usado por ambos os painéis, de modo que Documentos e Notícias compartilhem a mesma regra. Alternativa: duplicar `resumo_integro` no lote de notícias — simples, mas perpetua a divergência que causou o problema.

### 3. Falha de IA do guidance registrada em memória de sessão, com reabilitação

Registrar, no estado do serviço de guidance da sessão, os RGs cuja última tentativa de IA falhou, distinguindo "IA tentou e falhou" de "nunca tentou". A pendência acionável exige IA funcional e ausência de falha registrada no escopo da sessão; a reabilitação ocorre por reconfiguração do provedor, por uma nova sessão de uso (o registro é volátil) ou quando uma nova avaliação por IA concluir com sucesso. Preferir o registro em memória ao persistido no ledger para não alterar o schema v2 nem exigir migração; o ledger continua guardando método, data, caminho e resultado. Alternativas: (a) persistir a falha no ledger com timestamp — muda o schema e requer política de expiração; (b) tratar a IA como "disponível" somente quando funcional — não há como aferir funcionalidade sem chamada; (c) apenas logar a falha — não desliga o botão. O log silencioso atual (`_tentar_llm` engole `LLMError`) deixa de ser o único sinal.

### 4. Normalização da data de referência com hora

Interpretar `DD/MM/AAAA HH:MM[:SS]` descartando a hora, com fallback para a data da aquisição. Preferir um helper dedicado na normalização de datas (reusável por documentos relevantes e material facts) a um `strip` por regex no ponto de uso, para que a regra seja testável isoladamente. Alternativa: manter o fallback atual — re-download recorrente.

### 5. Registro de URL em store próprio, espelhando `content_hashes`

Novo store JSON por escopo (`url-downloads/<TICKER>.json` para documentos; `<cache>/noticias/url-downloads.json` global), com chave = URL normalizada e valor = caminho relativo canônico. Consulta antes do `_baixar`/`request`; gravação após download e persistência bem-sucedidos; poda junto de `podar_documento`/`podar_noticia`. Alternativa: estender o registro de hash de conteúdo — não serve, pois a meta é evitar a requisição antes do conteúdo existir. O registro é complementar: o hash de conteúdo continua tratando conteúdo idêntico vindo de URLs distintas.

### 6. Notícias: apontador não resolvido permanece pendente, ausência definitiva não

A exclusão da pendência vale apenas para ausência conclusiva (corpo somente em branco ou marcador). Corpo que é apontador para documento vinculado não resolvido continua pendente, conforme `noticias-panel` — Documento vinculado sob demanda. Alternativa: expirar apontadores antigos — rejeitada por poder descartar um vínculo que fica disponível depois.

## Risks / Trade-offs

- [URL mutável servida no mesmo endereço] → a URL registrada seria pulada com conteúdo novo. Mitigação: documento CVM é imutável por premissa; a poda libera a URL quando o arquivo some; quando houver versão/protocolo, registrá-lo como parte da chave.
- [Excluir sem-texto pode mascarar falha transitória] → Mitigação: excluir somente quando o texto é conclusivamente ausente; `PARCIAL`, `FALHA` e `PROTEGIDO` continuam pendentes (permanece a retentativa).
- [Registro de falha de IA em memória perde-se ao reiniciar] → Mitigação: aceitável; na nova sessão o RG volta a ser acionável e é tentado de novo, sem reter estado incorreto entre execuções.
- [I/O adicional no worker ao pré-computar sem-texto] → Mitigação: leitura no mesmo worker que já lê catálogo/ledger; para notícias, apenas o shard do ano/mês da faixa visível.
- [Regenerar muitos resumos de notícias consome cota de LLM] → Mitigação: só resumos sem pontuação final; a regeneração ocorre no lote acionado pelo usuário, com progresso e cancelamento.

## Migration Plan

Sem migração obrigatória. O registro de URL é populado conforme os downloads ocorrem (URLs ainda não registradas baixam uma vez e passam a ser lembradas) e o registro de falha de IA é volátil (por sessão), sem tocar no schema do ledger. Rollback: remover a consulta ao registro de URL e os filtros de texto das pendências restaura o comportamento anterior.

## Open Questions

Nenhuma pendente.

