## Context

As seis ações de atualização existem hoje apenas pela GUI: a carga de fundamentos é disparada pelo `FlowScopeController` e o job `executar_fundamental`; documentos e notícias são orquestrados direto por adaptadores de infraestrutura montados no `WiringMixin`; o resumo em lote vive em `presentation/gui/resumos_job.py` e depende de um painel Tk. As dependências de composição (repositórios, providers de fundamentos, fábrica de LLM) só existem dentro do mixin da GUI e, parcialmente, em `montar_core_navegacao` (`cli.py`). O MCP é estritamente somente-leitura por spec (`mcp-server`). Ver `proposal.md` para a motivação.

## Goals / Non-Goals

**Goals:**

- Expor as ações de atualização por uma CLI headless agendável, com paridade de comportamento com a GUI.
- Manter o MCP somente-leitura, expondo a data de referência como consulta.
- Tornar segura a escrita concorrente entre CLI e GUI.

**Non-Goals:**

- Tools de ação no servidor MCP (decidido fora de escopo).
- Concorrência fina por recurso (por ticker) ou lock não-bloqueante otimista.
- Alterar o layout dos caches ou o comportamento da árvore de conhecimento além do novo nó.

## Decisions

### Núcleo de composição neutro (`montar_nucleo`) — opção B

Extrair para um módulo neutro a composição hoje embutida no `WiringMixin._wire_controller` (cache, aquisições, dedup, grafo de fundamentos, stores, `B3MarketPriceFromResult`, fábrica de LLM). GUI, CLI e MCP passam a consumir o mesmo objeto; a GUI fica só com o que é dela (presenter, background, view).

- **Alternativa A** (composição headless própria, duplicada): menor risco imediato, mas cria uma segunda composição que diverge com o tempo. Rejeitada em favor do anti-duplicação do projeto.
- **Alternativa C** (cada superfície compõe as próprias dependências): duplicação explícita. Rejeitada.

### Núcleo do lote de resumos para a aplicação — opção D1

Extrair a orquestração do lote (`executar_resumos` e o protocolo do painel) e a lógica de preparação de texto (extração + persistência, incluindo a resolução do documento vinculado da "Geral" via CVM RAD/FNET) para a camada de aplicação. A GUI e a CLI expõem painéis finos sobre o mesmo núcleo.

- **Alternativa D2** (painel headless reimplementando a preparação em `presentation`): menor risco imediato, mas duplica ~80 linhas e a lógica de vínculo CVM/FNET, propensa a divergir. Rejeitada.

### Fundamentos executam a análise de mercado antes — opção E1

`atualizar fundamentos` roda a análise de mercado da data e reusa `B3MarketPriceFromResult(daily)` como `MarketPricePort`, replicando a carga da GUI. Alternativas E2 (sem mercado) degradaria Preço Típico e fallbacks de cotação/extremos em silêncio; E3 (flag) adiciona superfície sem necessidade.

### Exposição da data de referência — opção F2

O nó `/fundamentos/data-referencia` é o substrato (visível ao Chat AI e legível por `obter`); sobre ele há uma operação canônica `data_referencia` no núcleo, uma tool MCP e um subcomando CLI. Alternativa F1 (somente nó) não atende ao pedido de tool e comando dedicados e amarraria um valor operacional a um caminho mutável.

### Marcador `last_fundamentals` com fallback — opção B+A

Registrar `{data, fetched_at}` em `config.json` na conclusão da carga de fundamentos, pela CLI e pela GUI; resolver com fallback para `last_date`. Alternativa de unificar em `last_date` foi descartada porque `last_date` é preferência de UI (escrita só no fechamento da GUI) e nunca é tocada pela CLI, então não reflete a última carga agendada. Uma única função de resolução alimenta nó, operação, tool e comando.

### Escrita concorrente — M1 + M3 + M4

- **M1**: toda escrita atômica usa temporário de nome único por escrita e promoção com substituição que sobrescreve o destino. O `_atomic_write_bytes` atual usa nome de temporário determinístico (`<arquivo>.tmp`), que colide entre processos. Correção independente da concorrência.
- **M3**: lock global de ação baseado em arquivo, adquirido por cada subcomando de escrita e liberado pelo sistema operacional ao fim do processo (sem lock órfão). Política `--esperar <s>` ou falha rápida `operacao_em_andamento`.
- **M4**: a GUI adquire o mesmo lock nas fases de gravação, sem retê-lo durante toda a sessão.

Alternativas M2 (lock por store) e M5/M6 (estrutural/otimista) foram consideradas robustez futura; o lock global também serializa o consumo de RPM/cota dos provedores, que hoje é por processo.

### CLI verbo-primeiro — FORMA 2

`carregar watchlist`, `atualizar fundamentos|documentos|noticias`, `resumir documentos|noticias`, espelhando a família `nav`. Alternativa FORMA 1 (recurso→verbo) foi preterida por criar verbos de topo que são famílias novas.

## Risks / Trade-offs

- **[Lock global serializa ações independentes]** → aceitável para agendamento; granularidade fina fica como evolução.
- **[GUI esperando uma ação longa da CLI]** → a GUI adquire o lock só nas fases de escrita e a CLI oferece `--esperar` com limite; o usuário pode encerrar.
- **[Extração do lote mexe em mixins da GUI]** → coberta por testes de apresentação existentes; a lógica pura migra para a aplicação com testes próprios.
- **[Marcador obsoleto entre cargas]** → escrito nos dois pontos de carga (GUI e CLI) e com fallback; `fetched_at` permite detectar staleness.

## Migration Plan

Sem migração de formato: `config.json` ganha um bloco novo e os caches existentes permanecem válidos. Rollback consiste em remover os subcomandos e a tool nova; o bloco `last_fundamentals` é ignorado por versões anteriores. A correção M1 é retrocompatível.

## Open Questions

Nenhuma pendente.
