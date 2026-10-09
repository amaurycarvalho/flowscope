## Context

Ver `proposal.md` — Why. O log da aplicação é configurado em `presentation/main.py::_configure_logging`, que instala `_MillisecondFormatter` em todos os handlers (arquivo rotativo, syslog e NT Event Log) via `logging.basicConfig`. Há cerca de 60 handlers de aquisição que registram exceções com `exc_info=True`; a maioria é falha de rede tolerada. Já existe um antecedente de decisão registrada em spec (ver `engineering-standards`, requisito sobre validação OpenSpec em português).

## Goals / Non-Goals

**Goals:**
- Uma única linha concisa para falhas de comunicação, com tipo + mensagem, em todos os handlers de rede.
- Não alterar os call sites em massa; cobrir também pontos futuros.
- Manter `record.exc_info` intacto para testes (ex.: `test_fundamental_fallback`).
- Preservar tracebacks de erros inesperados (parsing, lógica, I/O local).

**Non-Goals:**
- Reclassificar a severidade dos eventos (permanece `WARNING`).
- Alterar as mensagens de domínio já concisas (`repository.py`, `noticias_vinculo.py`).
- Introduzir dependência nova de HTTP.

## Decisions

### Decisão 1: Tratar no formatter, não em cada call site

Adicionar `_CommunicationAwareFormatter(_MillisecondFormatter)` e usá-lo em `_configure_logging`. Ao formatar um registro cujo `exc_info` (ou sua cadeia de `__cause__`/`__context__`) contém `requests.RequestException`, o formatter:
1. copia o `LogRecord` (para não mutar o registro compartilhado entre handlers);
2. zera `exc_info`/`exc_text` na cópia;
3. formata normalmente e anexa ` [Tipo: mensagem]`.

**Por quê:** cobre dezenas de call sites (diretos e futuros) sem edições repetitivas e sem risco de regressão em cada um; mantém a convenção num único ponto.

**Alternativas:** (a) reescrever ~60 handlers adicionando um ramo `except requests.RequestException` — muito volume, duplicação e risco; (b) filtro por `logger` — o detalhe da exceção precisa ser anexado à mensagem, o que é responsabilidade do formatter; (c) não fazer nada — mantém o ruído.

### Decisão 2: Detectar pela cadeia de exceções

A causa é procurada em `exc.__cause__`/`exc.__context__`, para cobrir erros de domínio que encapsulam a falha de rede (ex.: `NetworkError(str(erro)) from erro` no cliente do Fundamentus).

**Por quê:** sem isso, `NetworkError` continuaria com traceback, contrariando o objetivo.

### Decisão 3: Preservar o `exc_info` no registro original

Só a cópia é alterada. Assim `caplog.records[i].exc_info` permanece preenchido e os testes existentes seguem válidos; apenas o texto renderizado omite o traceback.

## Risks / Trade-offs

- [Ocultar defeito real travestido de `RequestException`] → o resumo `[Tipo: mensagem]` permanece na linha, permitindo diagnóstico; exceções fora da árvore `requests` mantêm o traceback.
- [Duplo tratamento com o ajuste de `noticias_vinculo.py`] → inofensivo; aquele ponto mantém mensagem de domínio explícita e o formatter apenas não tem o que omitir.
- [Handlers de syslog/Event Log] → compartilham o mesmo formatter, então a saída fica consistente em todos os destinos.
