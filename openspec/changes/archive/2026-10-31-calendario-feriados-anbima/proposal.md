## Why

O FlowScope decide o que é dia útil por uma lista estática em `domain/b3/calendario.py`, que já está errada para 2026 e 2027 (falta 20/11/2026; Carnaval e Corpus Christi de 2027 estão em datas diferentes das publicadas pela ANBIMA). O calendário dinâmico por ano foi copiado de outro projeto, está órfão, importa `b3_selic_pre` e não roda. Além disso, o botão “Hoje” usa UTC e pode carregar a data errada para usuários fora do fuso universal. O resultado é consulta a dias sem pregão, HTTP 400 recorrente e cargas com data de referência incorreta.

## What Changes

- **Adotar o calendário ANBIMA como fonte única de feriados por ano**, com origem por feriado, normalização de datas/nomes, validação do dia da semana, cache em arquivo por ano, TTL por recência, cache negativo para ano futuro não publicado, fallback para cache anterior e modo degradado somente-fim-de-semana.
- **Recuperar e adaptar o subsistema de calendário já copiado**: renomear `b3_selic_pre` para `flowscope`, corrigir caminhos de cache, usar o lock/escrita atômica existentes e manter compatibilidade com Python 3.10.
- **Remover a lista estática de feriados** e fiar a verificação de dia útil em uma porta de aplicação alimentada pelo cache do calendário.
- **Garantir o calendário do ano da data de referência antes das cargas**, de forma best-effort: falha do calendário não bloqueia a carga principal, que segue com cache anterior ou apenas fim de semana.
- **Resolver a data de referência para o dia útil anterior** quando ela cair em fim de semana ou feriado. A amostragem existente continua avançando para o próximo dia útil, preservando o contrato de `sampling-strategy`.
- **Corrigir o botão “Hoje” e o `maxdate` do DateEntry** para usarem a data local do processo, não UTC.
- **Expor consulta e exportação**: CLI com `consultar feriados`, `exportar feriados` (CSV/JSON) e `atualizar feriados`; MCP com tools `calendario_*` somente-leitura e somente-cache, sem gravar arquivos.
- **Adicionar a aba `Feriados` na GUI**: árvore ano/mês/dia construída apenas do cache, textbox somente leitura, botão de atualização com `view-refresh`/`content-loading`, atualização em background e seleção preservada.
- **Manter 24/12 e 31/12 como recesso local da B3**, complementando a ANBIMA quando caem em dia de semana e não estão na página.
- **Fora de escopo**: a janela de evolução de 7/14/21/28 dias, por não ter consumidor no FlowScope atual.

## Capabilities

### New Capabilities

- `calendario-feriados`: fonte ANBIMA por ano, origem por feriado, normalização, cache/TTL, fallback, housekeeping, resolução de dia útil, atualização junto das cargas, concorrência/escrita atômica e consulta/exportação de dados.

### Modified Capabilities

- `data-ingestion`: a definição de dia útil deixa de vir da lista estática e passa a vir do calendário ANBIMA cacheado, com fallback somente-fim-de-semana.
- `sampling-strategy`: a fonte de feriados passa a ser o calendário dinâmico; o ajuste para o próximo dia útil permanece.
- `gui-interface`: o botão “Hoje”, o fallback da data de referência e o `maxdate` do DateEntry passam a usar a data local; a aba `Feriados` passa a existir.
- `cli-interface`: novos subcomandos `consultar feriados` e `exportar feriados`.
- `cli-acoes-atualizacao`: novo recurso `atualizar feriados` para revalidar anos no agendador.
- `mcp-server`: novas tools `calendario_listar`, `calendario_classificar` e `calendario_exportar`, somente-leitura e restritas ao cache.

## Impact

- **Domínio**: `domain/b3/calendario.py` (lista estática removida) e `domain/calendar.py` (modelos puros reutilizados, com origem por feriado).
- **Aplicação**: `application/calendar/*` (portas, configuração e serviço recuperados/adaptados); `application/use_cases.py` passa a receber a porta de dia útil; a classificação devolve a origem do feriado.
- **Infraestrutura**: `infrastructure/calendar/*` (fonte, parser, cache, storage, housekeeping e fábrica); `infrastructure/b3/client.py`, `infrastructure/b3/calendar.py` e `infrastructure/b3/repository.py` passam a usar o calendário dinâmico.
- **Apresentação**: composição (`composicao.py`), CLI (`cli.py`, `cli_consultas.py`, `cli_acoes.py`), MCP (`navegacao`/catálogo) e GUI (barra superior e nova aba `Feriados`).
- **Dados**: novo diretório `calendar/` sob o cache raiz do FlowScope, um JSON por ano, com lock dedicado `calendar.lock`.
- **Testes**: parser com fixture HTML real da ANBIMA, cache/TTL/fallback/housekeeping, integração com as cargas, fuso local, árvore da aba e tools MCP.
- **Documentação**: `docs/misc/datasources.md` (fonte ANBIMA e cache) e `docs/misc/panels.md` (aba `Feriados`).
- **Compatibilidade**: sem dependência nova; o comportamento de amostragem não muda.
