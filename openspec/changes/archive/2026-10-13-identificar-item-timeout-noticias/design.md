## Context

Ver `proposal.md` — Why. Pontos do estado atual que moldam a abordagem:

- O watchdog central (`src/flowscope/presentation/gui/background/manager.py`) decide a inatividade por `agora - handle.ultima_atividade > limite`. `ultima_atividade` é atualizada apenas quando o worker publica um evento (`_publicador`) e no início do job. Entre o progresso de um item e o próximo, uma extração longa é invisível.
- O `JobHandle` não tem descritor de item; `_aplicar_watchdog` loga só `id` e `grupo`.
- O lote de resumos (`src/flowscope/presentation/gui/resumos_job.py`) publica apenas contagens; nada do item corrente chega ao gerenciador.
- Para notícia "Geral" com apontador, `NoticiasPanel._texto_do_arquivo` chama o resolvedor injetado `baixar_conteudo_vinculado` (`src/flowscope/infrastructure/b3/noticias_vinculo.py`), que faz GET/POST com `TIMEOUT=30s` e até 3 tentativas, em 1–2 requisições sequenciais, e parseia o PDF baixado com `extrair_pdf` **sem orçamento**. Pior caso bem acima de 120s.
- O orçamento `EXTRACAO_TIMEOUT_S = 90s` (`src/flowscope/application/extracao_orcada.py`) só cobre o parse local de PDF por arquivo, com o processo filho lendo de um caminho. O invariante registrado é orçamento < `LIMITE_INATIVIDADE_S` (120s).
- A escalada de retry (`app_resumos_finalizacao.py`) cresce 30% o `timeout_extracao()` do painel e o `limite_inatividade_s` do gerenciador, sempre relativos ao valor em memória.

## Goals / Non-Goals

**Goals:**
- Identificar no log o item em processamento quando o watchdog encerra o job involuntariamente.
- Garantir que a resolução do documento vinculado (rede + parse) respeite o orçamento por item do painel, ficando abaixo do limite de inatividade.
- Tornar o parse do PDF baixado (em memória) sujeito ao mesmo orçamento e à mesma classificação de estados.
- Preservar o comportamento atual em sucesso e em falha tolerada (captcha/rede/formato): corpo original mantido, item pendente, sem exceção.

**Non-Goals:**
- Não redesenhar o watchdog nem trocar a unidade de "progresso" (continua por evento publicado).
- Não introduzir heartbeat para downloads legítimos longos (decisão do usuário: limitar pelo orçamento).
- Não alterar as constantes de retry/rede dos hosts nem a política de erro HTTP.
- Não persistir o orçamento nem o limite escalados.
- Não alterar o fluxo de senha nem a classificação parcial/protegido de notícia.

## Decisions

### D1. Descritor de atividade no `JobHandle`, via `JobContext.descrever`

Adicionar `descricao: str = ""` a `JobHandle` e um método `JobContext.descrever(descricao)` que apenas grava o texto no handle, **sem** atualizar `ultima_atividade`. Assim o watchdog continua detectando travamento (não é um progresso) mas passa a ter o item para logar; incluir `handle.descricao` nos dois avisos de `_aplicar_watchdog` (inatividade e thread morta).

- Alternativa descartada: logar o item no próprio worker antes de cada extração e inferir o item pela última linha. Não garante que o watchdog (que decide de forma assíncrona em `drenar`) nomeie o item no mesmo aviso e mistura a linha do watchdog com a do worker.
- Alternativa descartada: usar `handle.chave` (já usada pelo agendador). Reaproveitá-la acoplaria diagnóstico e política de agendamento.

### D2. O lote marca o item corrente antes de cada extração/resumo

Em `resumos_job._preparar_textos`, chamar `ctx.descrever(f"{arquivo.ticker}/{arquivo.nome}")` antes de `preparar_texto`; em `_resumir`, antes de `gerar_resumo_do_lote`. Em `finalizacao_job`, o mesmo por item. A descrição é por item, não por fase.

- Alternativa descartada: descrever apenas a fase ("Preparando textos"). Menos útil: não identifica a notícia.

### D3. Orçamento total (deadline) na resolução do documento vinculado

`baixar_conteudo_vinculado` ganha um parâmetro opcional de orçamento total (`timeout_total`). Quando informado, calcula um deadline (`monotonic() + timeout_total`) e o aplica a **toda** a operação: cada requisição usa `min(TIMEOUT, restante)`; antes de cada requisição (incluindo o segundo GET do FNET e o POST do CVM) aborta se o restante esgotou; o parse do PDF usa o restante. Sem o parâmetro, o comportamento atual é preservado.

- Alternativa descartada: reduzir `TIMEOUT`/`TENTATIVAS` globalmente. Ficaria abaixo de 120s, mas degradaria hosts legitimamente lentos e não cobriria o parse do PDF.
- Alternativa descartada: rodar o resolvedor em subprocesso com timeout. Custo alto (IP, sessão `requests`, payloads) para um problema que o deadline resolve na origem.

### D4. O painel deriva o deadline do seu orçamento corrente

`NoticiasPanel._texto_do_arquivo` passa `timeout_total=self.timeout_extracao()` ao resolvedor. Como a escalada de retry cresce esse orçamento e o limite de inatividade juntos (30%), o deadline da resolução fica sempre abaixo do limite vigente.

- Alternativa descartada: usar a constante fixa `EXTRACAO_TIMEOUT_S` dentro do resolvedor. O retry não folgaria o vínculo, contrariando a escalada e mantendo falhas legítimas após um timeout.

### D5. Contrato do resolvedor injetado aceita o orçamento opcional

O painel chama o resolvedor com `(texto, senha, timeout_total=...)`. O contrato de injeção (spec `noticias-panel`) passa a prever esse parâmetro opcional; o resolvedor de produção o respeita. Um resolvedor sem suporte ao parâmetro continua válido quando chamado sem ele, mas o painel o informa sempre — os dublês de teste são atualizados.

- Alternativa descartada: inspecionar a assinatura e chamar com/sem o parâmetro conforme o suporte. Esconde incompatibilidades que a spec quer tornar explícitas (regressão recente do vínculo).

### D6. Extração orçada de PDF a partir de bytes

Adicionar `extrair_pdf_com_orcamento(dados: bytes, senha=None, *, timeout=EXTRACAO_TIMEOUT_S)` em `extracao_orcada.py`, espelhando `extrair_arquivo_com_orcamento`, reusando `_consumir`/`_Acumulado`/`_finalizar`/`_configurar_log_pypdf` e um novo alvo de processo filho que recebe os bytes. O parse do PDF baixado em `noticias_vinculo._texto_do_documento` passa a usá-lo com o restante do deadline; HTML baixado continua sem orçamento (coerente com a spec).

- Alternativa descartada: gravar o PDF baixado em arquivo temporário e reusar `extrair_arquivo_com_orcamento`. Introduz I/O e limpeza de temporários sem necessidade.

### D7. Diagnóstico do item ao esgotar/ falhar a resolução

Como o resolvedor degrada para `None` em qualquer falha (captcha, rede, formato, orçamento), `NoticiasPanel._texto_do_arquivo` registra um `WARNING` nomeando a notícia quando, após tentar resolver, o corpo permanece um apontador não resolvido. Isso cobre explicitamente o caso de orçamento esgotado (a notícia que "demorou demais") sem depender de distinguir o motivo no resolvedor.

- Alternativa descartada: o resolvedor levantar/retornar um motivo estruturado. Ampliaria o contrato além do necessário; o painel é quem conhece a notícia e a condição de apontador pendente.

## Risks / Trade-offs

- [Deadline cortar downloads legítimos no limite] → O orçamento (90s) é folgado para os hosts suportados e cresce 30% no retry confirmado; itens cortados permanecem pendentes e são retentados, sem perda de dados.
- [Bytes do PDF copiados para o processo filho (`spawn`)] → Custo proporcional ao PDF baixado; os PDFs de vínculo são tipicamente pequenos e o caminho atual já carrega os bytes em memória.
- [Heurística de log de apontador pendente gerar ruído] → Um `WARNING` por notícia por execução do lote/pré-visualização; informativo e limitado ao escopo processado.
- [Dublês/tests do contrato do resolvedor quebrarem com o novo parâmetro] → Atualizar os dublês junto; o resolvedor de produção e os testes de assinatura cobrem a regressão.
- [Descrição desatualizada se o worker não a limpar] → A descrição é sempre reescrita antes de cada item; no término, o job sai do registro e a descrição não é reaproveitada.
- [Orçamento da resolução somar ao orçamento do parse local] → O deadline é único e compartilhado entre rede e parse do vínculo; o parse local do corpo HTML não consome orçamento.

## Migration Plan

Sem migração de dados nem de formato. As mudanças são de execução em memória (descritor, deadline) e não persistem estado. Rollback: remover o parâmetro de orçamento e a descrição restaura o comportamento anterior; nenhuma estrutura persistida é alterada.

## Open Questions

- Texto exato do aviso ao esgotar o orçamento e do log de apontador não resolvido — ajustável sem impactar specs ou abordagem.
- Se a pré-visualização individual (não só o lote) também deve marcar a descrição no watchdog — a princípio sim, por baixo custo; confirmável na implementação.
