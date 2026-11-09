# Design

## Context

Ver `proposal.md` para a motivação e os deltas de spec para os contratos. O estado atual que molda a solução:

- `controller_performance.executar_performance` calcula em background na GUI, grava `JsonPerformanceCache` (arquivo hasheado por `schema|índice|data|período|amostragem|tickers|base`) e publica um payload sem `ref_date`, período ou amostragem.
- `atualizar_fundamentos` já executa `AnalyzeTickersUseCase`, produzindo `resultado[ticker]["daily_data"]`, e a análise fundamentalista, produzindo a classificação. Hoje descarta os intermediários e retorna apenas contagens.
- O núcleo de navegação monta a árvore em `montar_core_navegacao` (headless) e em `ChatPanel.montar_arvore` (GUI), agregando fontes por ramo. O manifesto em `application/chat/manifesto.py` anuncia apenas ramos presentes.
- A preparação do MCP (`_preparar_mcp`, em `cli.py`) já roda `carregar watchlist` e `atualizar fundamentos` sob o lock global, com progresso em `stderr`, antes de servir.
- A CLI de leitura segue `exportar <recurso>` para dados locais e `consultar <recurso>` para dados remotos; `exportar feriados` usa `;` como separador.
- Fronteiras: `presentation -> application -> domain`; `infrastructure` só faz I/O/cache e não é importada por `application`.

## Goals / Non-Goals

**Goals:**

- Calcular, persistir, navegar e exportar a Performance sem GUI.
- Manter uma única visão do resultado mais recente entre GUI, chat, `flowscope nav` e MCP.
- Reusar os cálculos e provedores existentes, sem nova dependência.
- Fazer a preparação do MCP refletir a Performance quando `--data` for informado.
- Registrar problemas recuperáveis e edge cases sem poluir `stdout` nem o log do chat.

**Non-Goals:**

- Adicionar flags de período/amostragem ao headless nesta mudança; o padrão continua 30 dias/Fibonacci.
- Criar tools MCP `performance_*`; a navegação usa `nav_*`.
- Ajustar eventos societários ou mudar a regra de cálculo existente.
- Persistir múltiplos snapshots por configuração; o snapshot é o “mais recente”.
- Alterar o contrato do cache hasheado existente.

## Decisions

### D1 — `atualizar performance` separado, chamado pelo MCP após os fundamentos

Novo subcomando `flowscope atualizar performance [--data]`, sob o lock global, e a preparação do MCP passa a chamar, nesta ordem:

```text
carregar watchlist
  -> atualizar fundamentos  (devolve a data resolvida R)
  -> atualizar performance --data R
  -> montar árvore com reference_date=R
  -> servir
```

Motivo: mantém o custo de índice/proventos explícito e evita acoplar toda atualização de fundamentos a uma chamada de rede adicional. Alternativas descartadas: embutir sempre em `atualizar fundamentos` (custo surpresa) e calcular apenas na GUI (não atende ao headless).

Consequência aceita: quem rodar apenas `atualizar fundamentos` não terá Performance nova; precisa de `atualizar performance` ou da preparação do MCP com `--data`. Isso deve constar no help e no log.

### D2 — Snapshot estável e auto-descritivo

Além do cache hasheado, gravar `~/.cache/flowscope/performance/latest.json` com:

```text
schema_version, source, ref_date, period_days, sampling_method,
cached_at, benchmarks, default, ticker_types, results[benchmark]
```

Escrita atômica; leitura tolerante a ausência, JSON inválido, `resultado` não-dicionário e schema divergente. O snapshot é a fonte de leitura do chat, `nav`, MCP e `exportar performance`.

Motivo: o cache hasheado não é descobrível nem carrega o contexto necessário para a LLM. Alternativas descartadas: escanear e interpretar todos os arquivos hasheados (ambíguo e caro) e recalcular na navegação (viola o escopo somente-leitura).

### D3 — Mesma regra de montagem na GUI e no headless

Extrair a montagem do payload/snapshot para a camada de aplicação e reutilizá-la no job da GUI e em `atualizar performance`. O job da GUI passa a gravar o snapshot também.

Motivo: evitar divergência entre o que o painel mostra e o que o chat/MCP navegam. Alternativa descartada: manter dois formatos (payload da GUI e snapshot headless), que exigiria conversão e testes de equivalência.

### D4 — Configuração headless e contexto

`atualizar performance` usa `SamplingConfig()` (30 dias, Fibonacci), a mesma configuração já usada por `atualizar fundamentos`. O snapshot registra a configuração e a base de retorno, e a árvore expõe `/performance/configuracao`.

Motivo: os combos da GUI não são persistidos e o headless precisa de um default determinístico. Alternativa descartada: ler os combos da GUI (não existem fora da sessão) ou adicionar `--periodo`/`--amostragem` agora (escopo maior; fica como evolução).

### D5 — Aquisição de dados no headless

`atualizar performance` é autossuficiente: resolve a data, obtém `daily_data` dos trades em cache (recalculando a análise de mercado quando necessário), carrega a classificação do histórico de fundamentos e usa `AnalyzePerformanceUseCase` com o repositório de índices e o provedor de proventos existentes.

Na preparação do MCP, os intermediários de `atualizar fundamentos` podem ser passados em memória para evitar refazer a análise de mercado; standalone, o comando recalcula a partir do cache. O importante é que a fonte de verdade dos trades seja a mesma (`AnalyzeTickersUseCase`), preservando as datas amostradas.

Motivo: a Performance depende de `daily_data` já amostrado; ler todos os trades do cache poderia mudar as datas e o resultado. Alternativa descartada: montar `current_data` diretamente dos CSVs de trade.

### D6 — Política de falha

- **Duras:** watchlist ausente, data inválida, lock indisponível → `AcaoError`, código 1; a preparação do MCP aborta.
- **Recuperáveis:** índice indisponível, nenhum benchmark elegível, falha de um benchmark, falha de proventos → `WARNING`, resultado parcial e conclusão com sucesso; o MCP sobe e monta o que existir.
- **Snapshot:** falha de escrita gera `WARNING` e não derruba o cálculo; o snapshot anterior, se houver, permanece.

Motivo: a Performance é auxiliar; uma falha de índice não deve impedir o servidor MCP de servir fundamentos, documentos e notícias.

### D7 — Árvore e manifesto

```text
/performance
  /performance/configuracao
  /performance/benchmarks
    /performance/benchmarks/<BENCHMARK>/resumo
    /performance/benchmarks/<BENCHMARK>/tickers/<TICKER>
```

- Fonte `FontePerformance` em `application/chat`, recebendo o snapshot já carregado (não importa infraestrutura).
- `montar_core_navegacao` lê o snapshot via infraestrutura e injeta a fonte; `ChatPanel.montar_arvore` faz o mesmo com o snapshot disponível.
- Snapshot ausente/inválido: ramo omitido. Snapshot sem resultados: `configuracao` + folha de orientação com o motivo.
- Manifesto: `/performance` entra em `_RAIZES_DESCRICAO`, ganha descrição em `_RAMOS_CANONICOS` e uma linha no playbook, condicionada à existência do ramo.
- Resultados por ticker não entram em `_metadados`; apenas `configuracao`/`resumo` podem ser anunciados, para não estourar o teto de 4.000 tokens.

### D8 — Exportação CLI somente leitura

`flowscope exportar performance --formato <csv|json> [--benchmark ...] [--saida ...]` lê apenas `latest.json`.

- CSV com `;`, uma linha por ticker/benchmark, incluindo contexto (`ref_date`, `period_days`, `sampling_method`, `return_basis`, `index_available`) e campos por ticker.
- JSON com o snapshot estruturado.
- Sem snapshot → `performance_ausente`; benchmark ausente → `benchmark_ausente`; formato inválido → erro de argumentos.
- Sem recalcular, sem rede e sem lock.

Motivo: a exportação é leitura de dado local, como `exportar vwap`/`feriados`. Alternativa descartada: recalcular no export, que exigiria rede, lock e um contrato diferente.

### D9 — MCP sem tools novas

As tools `nav_*` já navegam qualquer ramo. O MCP só precisa montar a árvore com a fonte de Performance e manter o `stdout` limpo. Uma `performance_exportar` dedicada fica como evolução.

### D10 — Logging

- `INFO`: início/fim de `atualizar performance`, data resolvida, configuração, reutilização de cache, benchmarks calculados, escrita do snapshot.
- `WARNING`: índice indisponível, resposta inválida, proventos ausentes, ticker sem preço, menos de 2 observações, snapshot corrompido/schema divergente/defasado, falha de escrita, exportação sem snapshot, falha recuperável na preparação do MCP.
- `DEBUG`: ausência de snapshot na montagem da árvore por mensagem do chat, para não repetir `WARNING` a cada turno.
- MCP: todo log em `stderr`; `stdout` apenas JSON-RPC.

## Risks / Trade-offs

- **Análise de mercado duplicada no MCP** → passar os intermediários de `atualizar fundamentos` em memória na preparação; standalone recalcula do cache.
- **Snapshot defasado** → expor `ref_date` e `cached_at`, registrar `WARNING` quando a referência atual for mais nova; a árvore nunca inventa frescor.
- **Divergência GUI × headless** → uma única regra de montagem e escritor de snapshot; a config usada sempre vai no snapshot.
- **Cache hasheado e snapshot divergirem** → gravar ambos na mesma operação; o snapshot é a visão de leitura e o cache continua servindo o painel.
- **Manifesto acima do teto** → não incluir resultados por ticker em `_metadados` e manter a linha do playbook curta.
- **Endpoint de índice instável** → falha isolada por benchmark, `WARNING` com contexto e snapshot parcial; o MCP continua.
- **Leitura concorrente durante a escrita** → escrita atômica e leitura tolerante; um leitor pode ver a versão anterior, nunca um arquivo parcial.
- **Custo de rede no headless** → série do índice e proventos reusam cache; `atualizar performance` é explícito e sob lock.

## Migration Plan

- Nenhuma migração de dados. `latest.json` é descartável e pode ser removido sem perda; o cache hasheado existente continua válido.
- Rollback: remover o subcomando `atualizar performance` e a chamada na preparação do MCP, remover o ramo `/performance` do manifesto e ignorar o snapshot. A GUI e os demais ramos permanecem inalterados.
