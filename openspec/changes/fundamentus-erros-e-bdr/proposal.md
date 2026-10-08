## Why

Um BDR sem cobertura no Fundamentus (ex.: `EXXO34`) é hoje classificado como `LayoutChanged` ("layout alterado") e registrado em `WARNING` com traceback completo, mesmo sendo um "ticker não encontrado/sem dados" esperado e recuperável. Isso polui o log e **mascara regressões reais de layout**, além de gastar uma requisição de rede com um portal que não cobre BDRs.

## What Changes

- **Classificação de erro correta**: quando a página do Fundamentus não trouxer conteúdo utilizável (tabela/linhas vazias, sem dados de papel), o parser passa a sinalizar **`TickerNotFound`** em vez de `LayoutChanged`; `LayoutChanged` fica reservado ao caso em que a página **tem conteúdo parseável** mas faltam os rótulos obrigatórios (nome e cotação).
- **Log por tipo de erro**: o `CompositeFundamentalProvider` registra `TickerNotFound` em `INFO`, sem traceback; mantém `WARNING` com traceback apenas para `LayoutChanged` e `NetworkError` reais.
- **BDR não consulta o Fundamentus (campos e FFO)**: ativos classificados como `TipoAtivo.BDR` são pulados pela fonte Fundamentus no composto de **campos fundamentalistas** e no composto de **FFO**, sem chamada de rede; a análise segue com as demais fontes. Dividendos **não** mudam (continuam com o histórico do Fundamentus e a fonte dedicada de BDR).
- Sem quebra de contrato: tickers não-BDR mantêm o comportamento atual; erros de rede e layout continuam visíveis como antes.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a mudança é comportamental sobre capacidades existentes. -->

### Modified Capabilities

- `fundamentus-fundamental-provider`: distinguir "página sem dados" (`TickerNotFound`) de "layout alterado" (página com conteúdo, rótulos obrigatórios ausentes) e pular a consulta ao portal para tickers BDR.
- `fundamental-source-fallback`: registrar `TickerNotFound` em `INFO` sem traceback no composto de campos, preservando `WARNING` com traceback para falhas de layout/rede.

## Impact

- Código (alterado): `infrastructure/fii/fundamentus/parser.py` (classificação da página vazia), `infrastructure/fii/fundamentus/provider.py` (curto-circuito de BDR sem rede), `infrastructure/fii/fundamentus/adapter.py` (BDR sem campos do Fundamentus), `application/fundamental_fallback.py` (severidade do log), `presentation/gui/app_wiring.py` (injeção do classificador/predicado de BDR nos compostos de campos e FFO).
- Dependência: classificação existente `TipoAtivo.BDR` / sufixos 32–39 (`domain/fii/classification.py`), já usada em `_obter_dados_bdr`.
- Sem novas dependências. Testes: classificação de erro no parser/cliente, severidade de log no composto, e BDR pulando Fundamentus nos compostos sem chamada de rede.
