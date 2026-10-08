## Context

Ver `proposal.md` — Why. Estado atual relevante:

- `parse_ativo` (`infrastructure/fii/fundamentus/parser.py:155`) levanta `LayoutChanged` sempre que nome e cotação estão ambos ausentes, sem distinguir página vazia de layout alterado.
- `FundamentusClient.fetch_response` (`client.py:79-82`) já sinaliza `TickerNotFound` quando o HTML contém as pistas textuais `"nenhum papel encontrado"`/`"não encontrado"`.
- `CompositeFundamentalProvider.obter_com_resultado` (`application/fundamental_fallback.py:54-73`) captura qualquer exceção e loga `WARNING` com `exc_info=True`, sem separar o tipo de falha.
- A classificação já identifica BDR por sufixo (32–39) em `domain/fii/classification.py` (`TipoAtivo.BDR`, `classificar_ticker`), e `FundamentalDataMixin` já usa esse portão em `_obter_dados_bdr` (`application/fundamental_providers.py:116`).
- O Fundamentus alimenta os campos fundamentalistas via `FundamentusFundamentalDataProvider` (`infrastructure/fii/fundamentus/adapter.py`) e o FFO via `ffo_provider.FundamentusProvider.obter_ffo` (`infrastructure/fii/ffo_provider.py:111`), que faz `self._carregar(...)` (rede/cache) sem checar tipo.

## Goals / Non-Goals

**Goals:**
- Distinguir "página sem dados de papel" (`TickerNotFound`) de "layout alterado" na aquisição do Fundamentus.
- Fazer o composto de campos registrar ticker ausente como informativo (sem traceback), preservando avisos para layout/rede.
- Pular a consulta ao Fundamentus para tickers BDR nos caminhos de campos fundamentalistas e de FFO, sem chamada de rede.

**Non-Goals:**
- Alterar o caminho de dividendos (o histórico do Fundamentus e a fonte dedicada de BDR permanecem como estão).
- Detectar BDR por outra via que não a classificação existente.
- Mudar a ordem de prioridade das fontes para não-BDR.

## Decisions

### 1. Exceção de domínio `TickerNaoEncontrado`

Adicionar `TickerNaoEncontrado(Exception)` no domínio (novo `domain/fii/errors.py`, exportado). Fazer `infrastructure/fii/fundamentus/errors.py::TickerNotFound` herdar também de `TickerNaoEncontrado`.

- **Por quê**: o composto vive na aplicação e não pode importar o erro de infraestrutura; um tipo de domínio permite separar a severidade do log sem quebrar as camadas.
- **Alternativas**: o composto testar o nome da exceção (rejeitada: frágil e acopla por string); mover o erro para a aplicação (rejeitada: a distinção é semântica de domínio).

### 2. Página sem dados é `TickerNotFound`

Em `parse_ativo`, quando `coletar_raw` não produz **nenhum** par rótulo→valor (página sem tabela/linhas), levantar `TickerNotFound`; manter `LayoutChanged` quando há conteúdo parseável mas os rótulos obrigatórios (nome e cotação) faltam. O cliente continua detectando as pistas textuais explícitas.

- **Por quê**: separa o caso esperado (papel ausente/sem dados) da regressão de layout que exige atenção.
- **Trade-off**: uma quebra de layout que zere as linhas seria lida como "não encontrado"; mitigação: os testes de contrato com fixtures detectam a perda de rótulos obrigatórios.

### 3. Severidade do log por tipo de erro

No `CompositeFundamentalProvider`, capturar `TickerNaoEncontrado` primeiro e logar em `INFO` sem `exc_info`; manter `except Exception` com `WARNING` + `exc_info=True` para os demais (`LayoutChanged`, `NetworkError`, falhas inesperadas).

- **Por quê**: elimina o ruído de traceback para BDRs ausentes e mantém o sinal das falhas que exigem ação.
- **Alternativas**: baixar todo o log para INFO (rejeitada: esconde regressões reais); filtrar no adapter (rejeitada: o composto é o ponto único de registro).

### 4. BDR pula Fundamentus (campos e FFO)

Usar `classificar_ticker(ticker).tipo is TipoAtivo.BDR` para curto-circuitar:
- `FundamentusFundamentalDataProvider.obter_com_resultado`: BDR → retorna `{}` sem chamar o provider.
- `ffo_provider.FundamentusProvider.obter_ffo`: BDR → retorna `None` sem `self._carregar`.

- **Por quê**: o portal não cobre BDRs; evita requisição e aviso, e a análise segue com B3/CVM e o motor de FFO. Reusa o portão já empregado em `_obter_dados_bdr`.
- **Alternativas**: rotear por tipo no composto (rejeitada: exige conhecer a semântica da fonte na camada de composição); checar no cliente HTTP (rejeitada: o cliente não conhece classificação de ativo).

## Risks / Trade-offs

- **[Layout que zera as linhas vira "não encontrado"]** → trade-off aceito; os testes de contrato de fixture cobrem a perda de rótulos.
- **[BDR deixa de receber campos que o Fundamentus porventura tivesse]** → aceito: BDR tem fontes dedicadas (B3/CVM/BDR) e o comportamento fica alinhado ao portão existente.
- **[Exceção com herança múltipla]** → `class TickerNotFound(FundamentusError, TickerNaoEncontrado)` é simples; validar na implementação que capturas existentes de `FundamentusError` seguem funcionando.
- **[Divergência residual de avisos]** → FFO/`ffo_provider` ainda pode logar para BDR se consultado por outro caminho; mitigado pelo curto-circuito no `obter_ffo`.

## Migration Plan

- Mudança aditiva: nova exceção de domínio; comportamento de não-BDR inalterado.
- Rollback: remover os curto-circuitos de BDR e a exceção de domínio; reverter `parse_ativo` e a severidade do log.
