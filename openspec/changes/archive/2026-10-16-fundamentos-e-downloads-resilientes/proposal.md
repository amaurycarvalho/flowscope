## Why

A atualização de fundamentos ficou mais lenta e passou a devolver `N/A` no nome do ticker porque a fonte primária (Fundamentus) está indisponível: o certificado de `www.fundamentus.com.br` passou a cobrir apenas `fundamentus.com.br` (SAN sem `www.`), então toda chamada falha por *hostname mismatch*. Com a fonte primária fora, o composto consulta todos os fallbacks por ticker — incluindo hosts com instabilidade conhecida (FNET, `rad.cvm.gov.br`) — e os campos que só o Fundamentus fornecia (nome de ações/BDR, VP/Cota, dividendos, FFO, indicadores) somem sem aviso. Ao mesmo tempo, os downloads compartilhados por Documentos, Notícias e Fundamentos (informe/proventos) não validam conteúdo nem têm orçamento total por item, de modo que respostas não-desejadas se perdem em silêncio ou envenenam caches.

## What Changes

- **Fundamentos — fonte primária e identidade**
  - Corrigir o host do Fundamentus para o coberto pelo certificado (apex `fundamentus.com.br`), nos três endpoints (`detalhes`, `proventos`, `fii_proventos`) e no `robots.txt`.
  - Expor o **nome de exibição** a partir da identidade B3 já existente (`GetInitialCompanies`: `companyName`/`tradingName`) como fallback para ações/BDR, mantendo a listagem de fundos (`fundName`) para FII.
  - Tornar visível o **modo degradado**: registrar, por ticker, a fonte/URL que falhou, em vez de varrer silenciosamente toda a cadeia de fallback.
  - **Remover o fallback `empresas-listadas.csv`** (a URL foi desativada pela B3 e o host agora devolve `302`/HTML), deixando a resolução `ticker → codeCVM` **API-only** (`GetInitialCompanies`, já com o retry central). **BREAKING** apenas para o comportamento interno da resolução.
  - Deixar de **cachear falha como ausência**: só cachear `None` quando a API respondeu e não achou; falha de resolução (rede/HTTP) NÃO DEVE ser cacheada, evitando fixar a ausência por 30 dias.

- **Downloads resilientes compartilhados (Documentos, Notícias e informe/proventos)**
  - Centralizar o download de arquivos (PDF/HTML) em um helper único com **validação de conteúdo** (assinatura `%PDF` ou HTML esperado) e **orçamento total por item** (deadline), aplicado a: documentos relevantes (FNET), informe mensal (FNET), proventos/informe de fundamentals (FNET) e documentos vinculados de notícias (FNET e `rad.cvm.gov.br`).
  - **FNET**: repetir em resposta `200` não-PDF e tratar o `403` intermitente como repetível via override de ponto de chamada; opção de resolver via `visualizarDocumento` → `iframe exibirDocumento`.
  - **rad.cvm**: renovar token/sessão (novo GET da página) antes de repetir o POST `ExibirPDF`, com backoff; manter validação `%PDF`.

- **Robustez da carga e desfecho**
  - Tratar ausência de dados de negociação em **dia não útil** (ex.: feriado) como ausência, sem requisitar nem registrar erro (reforço do fix de feriados já existente).
  - Tornar o `fundamental_job` identificável no log do watchdog (descrição da atividade corrente com o ticker em processamento).
  - Distinguir **falha** de **nada novo** no desfecho da aquisição, na sub-aba Documentos (e de forma consistente em Notícias/Fundamentos).

## Capabilities

### New Capabilities
- `download-conteudo-resiliente`: aquisição de arquivos (PDF/HTML) com validação de conteúdo, orçamento total por item e sessão/token renovável, compartilhada por documentos relevantes, informe/proventos e notícias, sobre os hosts FNET e rad.cvm.

### Modified Capabilities
- `fundamentus-fundamental-provider`: uso do host coberto pelo certificado (apex) e comportamento de degradação controlada quando a fonte primária fica indisponível.
- `fundamental-source-fallback`: nome de exibição obtido da identidade B3 já existente para ações/BDR e registro da fonte indisponível por ticker.
- `code-cvm-resolution`: resolução `ticker → codeCVM` passa a ser API-only (sem o cadastro CSV) e deixa de cachear falha de resolução como `None`, distinguindo ausência de indisponibilidade.
- `documentos-relevantes-extraction`: download e validação passam a usar o helper resiliente (validação de conteúdo + orçamento).
- `noticias-panel`: resolução do documento vinculado (FNET/rad.cvm) passa a usar o helper resiliente, com renovação de sessão.
- `documentos-aquisicao-painel`: desfecho da aquisição distingue falha de ausência de novidades.
- `data-ingestion`: dia não útil (feriado) não é requisitado e a ausência de arquivo não é tratada como erro.

## Impact

- **Infraestrutura (rede/download)**: `infrastructure/fii/fundamentus/client.py` (hosts); `infrastructure/b3/funds_client/documentos.py` e `documentos_relevantes.py` (FNET); `infrastructure/b3/noticias_vinculo.py` e `infrastructure/cvm/pdf.py` (FNET/rad.cvm); novo helper compartilhado de download.
- **Infraestrutura (identidade)**: `infrastructure/b3/funds_client/code_cvm.py` (reaproveitar `GetInitialCompanies` para o nome; remover o fallback do cadastro e não cachear falha), `infrastructure/b3/funds_client/cvm.py` e `constants.py` (remover o índice/URL do cadastro) e `infrastructure/b3/fund_repository.py`.
- **Aplicação**: `application/fundamental_analysis.py` (`_resolver_nome`), `application/fundamental_fallback.py` (proveniência/degradado), `application/fundamental_providers.py`.
- **Apresentação**: `presentation/gui/fundamental_job.py` (`ctx.descrever`), `presentation/gui/app_actions.py` (desfecho honesto) e `presentation/gui/documentos_job.py`.
- **Dados de mercado**: `infrastructure/b3/calendar.py` / `domain/b3/calendario.py` (não requisitar dia não útil) e `infrastructure/b3/client.py`.
- **Specs tocadas**: `download-conteudo-resiliente` (nova), `fundamentus-fundamental-provider`, `fundamental-source-fallback`, `code-cvm-resolution`, `documentos-relevantes-extraction`, `noticias-panel`, `documentos-aquisicao-painel`, `data-ingestion`.
- **Sem dependências externas novas.** Sem mudança de contrato público de CLI/MCP.
