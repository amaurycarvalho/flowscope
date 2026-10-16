## Context

Ver `proposal.md — Why` para a motivação. Restrições que moldam o desenho:

- O motor de retry central (`infrastructure/http_retry.py`, spec `politica-erros-http`) classifica status e repete por exceção, mas **não inspeciona o corpo da resposta** e não tem orçamento total por item. A classificação de `403` como `PERMANENTE` é normativa; a flexibilização passa pelo *override de ponto de chamada* (`transitorios_extra`), já existente e usado em `regulatorio.py` (404 intermitente).
- O `noticias_vinculo.py` já implementa um **prazo total** (`_Prazo`) e o fluxo `visualizarDocumento → iframe`; os demais consumidores de FNET (`documents_relevantes`, `buscar_html_documento`, fundamentos informe/proventos) batem direto no `exibirDocumento` sem sessão/referer.
- O Fundamentus é a **fonte primária** da composição (`fundamental_fallback.py`); os fallbacks são B3 e CVM. O nome de ações/BDR só vem do Fundamentus hoje; o de FII vem de `fundName` (B3).
- A identidade B3 já é consultada por `GetInitialCompanies` (`code_cvm.py`), que devolve `companyName`/`tradingName`/`cnpj`, mas só o `codeCVM` é aproveitado.
- `B3FundRepository.find_by_ticker` e `B3FundamentalRepository` são orientados a **fundos**; não cobrem ações.
- A amostragem de datas já usa `is_business_day` (`domain/b3/calendario.py`), mas o fix de feriados é recente (commit `b647c69`).

## Goals / Non-Goals

**Goals:**
- Restaurar a fonte primária de fundamentos sem depender de afrouxar a verificação TLS.
- Fazer o nome de exibição sobreviver à queda da fonte primária reaproveitando identidade B3 já baixada.
- Um único caminho de download resiliente (validação de conteúdo + orçamento por item) compartilhado por Documentos, Notícias (vínculo) e informe/proventos de Fundamentos.
- Tornar falhas visíveis (por ticker e por desfecho), sem virar erro fatal.

**Non-Goals:**
- Não alterar a classificação central de status (`politica-erros-http`): o `403` do FNET entra por override local.
- Não introduzir dependência externa nova nem serviço.
- Não mudar contratos públicos de CLI/MCP.
- Não resolver captcha de visualizadores.

## Decisions

### 1. Host do Fundamentus = o coberto pelo certificado (apex)

Usar `https://fundamentus.com.br/...` (SAN do certificado) em `detalhes.php`, `proventos.php`, `fii_proventos.php` e `robots.txt`, derivando as URLs de uma única constante de host em `fundamentus/client.py`.

- *Alternativas rejeitadas:* desabilitar verificação TLS (inseguro); seguir redirect a partir do `www.` (o `www.` falha na verificação antes de redirecionar); fixar CA customizada (frágil, precisa re-sync).
- *Racional:* apex responde `200` nos três endpoints (verificado) e o SAN do certificado cobre exatamente esse nome.

### 2. Nome de exibição a partir da identidade B3 já existente

Estender a resolução de identidade para **expor o nome** junto do `codeCVM`, reaproveitando a mesma chamada `GetInitialCompanies` (cacheada):

- Novo método na camada de identidade (ex.: `obter_nome_negociacao(ticker)`), lendo `companyName`/`tradingName` do registro casado por `issuingCompany == raiz`.
- Injetar esse nome na análise como fallback de `CAMPO_NOME` quando a fonte primária não o fornecer, mantendo `fundName` para FII.

- *Alternativas:* usar CVM FCA/FRE para o nome (mais lento e já usado para CNPJ); novo endpoint dedicado (desnecessário).
- *Racional:* zero URL nova; a fonte já é consultada e cacheada.

### 2b. Resolução codeCVM API-only (remover o fallback CSV) e sem cachear falha

Remover o fallback `empresas-listadas.csv` e deixar `resolver_code_cvm` **API-only**: a URL antiga foi desativada pela B3 (a nova página "Empresas Listadas" usa a mesma API `GetInitialCompanies`, sem CSV) e o host devolve `302`/HTML, o que hoje gera índice vazio e envenena o cache por 30 dias. Além disso, `_fetch` NÃO DEVE capturar a falha e devolvê-la como `None`: em `RequestException` ele DEVE propagar, de modo que `get_or_fetch` não grave nada; o `None` só é cacheado quando a API respondeu sem correspondência (ausência real).

- *Alternativas:* manter o cadastro apontando para a nova URL (não existe CSV no novo portal — verificado no bundle da SPA); reconstruir o índice pela própria API em lote (mesmo host/API, não agrega disponibilidade).
- *Racional:* elimina uma dependência morta e o modo de falha silencioso, sem reduzir a resiliência real (o fallback já estava quebrado).

### 3. Download resiliente compartilhado

Criar um adaptador único (ex.: `infrastructure/download_resiliente.py`) que encapsula: resolução de URL (direta ou `visualizarDocumento → iframe`), `requests.Session`, `executar_com_retry` para status/erro de rede, um `_Prazo` (deadline) por item e **validação de conteúdo**.

- *Validação de conteúdo:* estender `executar_com_retry` com um parâmetro opcional `validar(resposta) -> bool`; quando o conteúdo não é válido, a tentativa é tratada como repetível (categoria transitória) e consome o orçamento. Mantém um único motor.
- *Orçamento:* o helper calcula o timeout efetivo de cada requisição como o restante do prazo (padrão de `noticias_vinculo._Prazo`) e interrompe ao esgotá-lo, sinalizando a falha do item.
- *FNET:* o ponto de chamada declara `transitorios_extra={403}`; quando configurado, o helper resolve via `visualizarDocumento` e segue o `iframe` com `Referer`.
- *CVM RAD:* o helper re-obtém a página (novo token/sessão) antes de nova tentativa do POST `ExibirPDF`.
- *Consumidores:* `baixar_pdf_documento`, `buscar_html_documento`, `baixar_pdf_cvm` e `noticias_vinculo` delegam ao helper; a política de cache/gravação de cada um permanece.

- *Alternativas:* loop local reimplementando retry/backoff em cada consumidor (duplicação); não validar conteúdo e confiar só no status (foi a causa do cache envenenado por challenge HTML).
- *Racional:* um ponto único para o comportamento exigido pela nova capability, sem tocar a classificação central.

### 4. Renovação de sessão no visualizador da CVM

Unificar os dois fluxos do `rad.cvm.gov.br` no padrão "GET página → POST `ExibirPDF`": ao falhar o POST, refazer o GET (token/sessão novos) antes de repetir, tudo sob o orçamento do item.

- *Alternativa:* apenas aumentar tentativas do POST com o mesmo token (o token pode já estar inválido → repetir não ajuda).
- *Racional:* a página é a origem do token; renová-la ataca a causa provável do `500` persistente.

### 5. Observabilidade e desfecho

- `FundamentalAnalysisUseCase.execute` ganha um callback opcional `on_item(ticker)` chamado **antes** de processar cada ticker; `fundamental_job.executar_fundamental` o liga a `ctx.descrever`, de modo que o watchdog nomeie o ticker no encerramento por inatividade.
- A aquisição de documentos passa a devolver um resultado com contagem de **novos/reutilizados/falhas**; `_finalizar_documentos` compõe a mensagem distinguindo falha de ausência.
- A composição de fontes registra (log) a fonte indisponível por ticker (hoje a mensagem existe para o Fundamentus; padronizar para as demais).

### 6. Dia não útil

Reforçar em `fetch_trades`/resolução de datas que **dias não úteis não são requisitados**, e classificar ausência/`400` em dia não útil como ausência de pregão (sem warning de erro), mantendo `is_business_day` como fonte única.

## Risks / Trade-offs

- [Certificado do Fundamentus voltar a mudar (incluir/remover `www.`)] → host derivado de constante única; um teste verifica o host efetivo; a troca fica localizada.
- [Validação de conteúdo consumir tentativas e alongar o pior caso] → orçamento total por item limita a duração; o helper é compartilhado, então o ajuste vale para todos.
- [Override de `403` mascarar bloqueio definitivo do FNET] → limitado pelas 4 tentativas e pelo orçamento; falha é sinalizada (não silenciosa).
- [Renovação de sessão dobrar requisições no `rad.cvm`] → só ocorre em falha do POST, sob o orçamento; evita repetir com token inválido.
- [Nome via `GetInitialCompanies` não cobrir certos papéis] → mantém ausência explícita (`N/A`) quando não houver identidade; sem regressão.
- [Remover o fallback CSV deixar a resolução sem alternativa quando a API cai] → o fallback já estava quebrado (índice vazio), então não há perda real; com o retry central e sem cachear falha, a próxima execução volta a tentar. Confirmar cobertura da API com amostra de ação/unit/BDR antes de remover.
- [Mudança de assinatura de retorno da aquisição de documentos]** → tocar também o caminho CLI (`cli-acoes-atualizacao`, change ativa); alinhar o contrato antes de implementar.
- [Alterar `executar_com_retry` afetar todos os acessos]** → parâmetro opcional e retrocompatível; sem mudança de comportamento quando ausente.

## Migration Plan

- Sem migração de dados. O cache `fundamentus_*` antigo é reaproveitado pela validação condicional (freshness/`safety_ttl`); não é necessário limpar.
- Rollback: reverter o host do Fundamentus e o uso do helper restaura o comportamento anterior.
- Ordem sugerida de entrada: (1) host do Fundamentus; (2) nome via identidade B3; (2b) resolução codeCVM API-only sem cachear falha; (3) helper compartilhado e consumidores; (4) observabilidade/desfecho; (5) dia não útil.
- Migração do cache: `cadastro_empresas_code_cvm.json` fica órfão e expira sozinho (30 dias); não requer limpeza manual.

## Open Questions

- Valor do orçamento total por item no helper (reusar o `EXTRACAO_TIMEOUT_S = 90` ou definir um orçamento de download próprio). Não muda specs nem o recorte de tarefas; calibrar na implementação com medição.
- Padrão exato da mensagem de desfecho com falhas (texto/ícone). Não muda comportamento observável além de "sinalizar falha".
