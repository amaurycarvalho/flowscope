## 1. Exceção de domínio

- [x] 1.1 Criar `TickerNaoEncontrado` em `domain/fii/errors.py`, exportá-la em `domain/fii` e verificar com um teste em `tests/test_domain/test_fii/` que a exceção é importável pelo pacote de domínio
- [x] 1.2 Fazer `infrastructure/fii/fundamentus/errors.py::TickerNotFound` herdar também de `TickerNaoEncontrado` e verificar, em `tests/test_infrastructure/test_fundamentus_provider.py`, que `isinstance(TickerNotFound(...), TickerNaoEncontrado)` é verdadeiro e que capturas de `FundamentusError` continuam valendo

## 2. Classificação da página sem dados

- [x] 2.1 Ajustar `parse_ativo` (`infrastructure/fii/fundamentus/parser.py`) para levantar `TickerNotFound` quando a página não tiver nenhum par rótulo→valor e manter `LayoutChanged` quando houver conteúdo parseável sem nome/cotação; verificar com `tests/test_infrastructure/test_fundamentus_provider.py` cobrindo página vazia (não encontrado) e página com conteúdo sem obrigatórios (layout)
- [x] 2.2 Garantir que a detecção textual do cliente (`"nenhum papel encontrado"`/`"não encontrado"`) continua sinalizando `TickerNotFound`; verificar com teste do cliente no mesmo arquivo

## 3. Severidade do log no composto

- [x] 3.1 Separar no `CompositeFundamentalProvider` (`application/fundamental_fallback.py`) a captura de `TickerNaoEncontrado` (INFO sem traceback) das demais falhas (WARNING com traceback); verificar com `tests/test_application/test_fundamental_fallback.py` usando `caplog` para o nível e a ausência de `exc_info` no caso de ticker ausente
- [x] 3.2 Preservar o comportamento de continuar para o fallback e a origem do primeiro contribuinte; verificar com os testes existentes do composto

## 4. BDR não consulta o Fundamentus (campos e FFO)

- [x] 4.1 Curto-circuitar BDR em `FundamentusFundamentalDataProvider.obter_com_resultado` (`infrastructure/fii/fundamentus/adapter.py`) com `classificar_ticker(...).tipo is TipoAtivo.BDR`, sem chamar o provider; verificar com teste do adapter em `tests/test_infrastructure/test_fundamentus_provider.py` que um BDR retorna vazio e o provider não é acionado
- [x] 4.2 Curto-circuitar BDR em `ffo_provider.FundamentusProvider.obter_ffo` (`infrastructure/fii/ffo_provider.py`) sem `self._carregar`; verificar com teste que um BDR retorna `None` sem chamada ao provider base
- [x] 4.3 Garantir que um ticker não-BDR continua consultando o Fundamentus normalmente; verificar com teste no adapter e no `obter_ffo`

## 5. Quality gate

- [x] 5.1 Rodar `make lint` e `make test` com sucesso; verificar que a cobertura permanece ≥ 85%
- [x] 5.2 Rodar `openspec validate fundamentus-erros-e-bdr` sem erros
