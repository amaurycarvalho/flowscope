## 1. Escrita concorrente (M1 + M3 + M4)

- [ ] 1.1 Alterar `infrastructure/conditional_cache_types.py::_atomic_write_bytes` para usar temporário de nome único por escrita (ex.: sufixo com `os.getpid()` + contador/uuid) e promoção com substituição que sobrescreve o destino; verificar com teste que duas gravações concorrentes do mesmo arquivo não falham nem deixam conteúdo parcial
- [ ] 1.2 Criar utilitário de lock de arquivo cross-process (stdlib `fcntl`/`msvcrt`) no cache padrão; verificar com teste que um segundo processo não adquire o lock enquanto o primeiro o detém e que o lock some ao encerrar o processo
- [ ] 1.3 Adicionar a aquisição do lock global de ação aos subcomandos CLI de escrita, com opção `--esperar <s>` e erro estruturado `operacao_em_andamento`; verificar com teste de dois comandos concorrentes
- [ ] 1.4 Fazer a GUI adquirir o mesmo lock nas fases de gravação dos jobs (fundamentos, aquisição de documentos/notícias, lote de resumos); verificar com teste de apresentação que a fase de escrita adquire e libera o lock

## 2. Núcleo de composição neutro (B)

- [ ] 2.1 Criar módulo de composição neutro com `montar_nucleo()` consolidando cache, aquisições, dedup, grafo de fundamentos, stores e fábrica de LLM hoje embutidos em `WiringMixin._wire_controller`; verificar que `montar_nucleo()` monta o grafo sem depender de Tk
- [ ] 2.2 Fazer `WiringMixin` consumir `montar_nucleo()` (mantendo os atributos que os mixins leem) e reexecutar os testes de apresentação afetados; verificar sem regressão
- [ ] 2.3 Fazer `cli.py::montar_core_navegacao` reusar `montar_nucleo()` em vez de recompor documentos/notícias; verificar que `flowscope nav listar /noticias/grupos` segue produzindo o mesmo JSON

## 3. Núcleo do lote de resumos para a aplicação (D1)

- [ ] 3.1 Extrair a preparação de texto (extração com orçamento + persistência de resultado definitivo) para a camada de aplicação, incluindo a resolução do documento vinculado da "Geral" (CVM RAD/FNET); verificar com testes de unidade da preparação
- [ ] 3.2 Mover a orquestração do lote (`executar_resumos` e o protocolo do painel) para a aplicação sobre uma interface mínima de progresso/cancelamento; verificar com testes do lote sobre um painel fake
- [ ] 3.3 Refazer `DocumentFlowMixin`/`NoticiasPanel` para delegar ao núcleo extraído, preservando o comportamento atual; verificar sem regressão nos testes de apresentação

## 4. Marcador e exposição da data de referência

- [ ] 4.1 Persistir `last_fundamentals` (`{data, fetched_at}`) em `config.json` ao concluir a carga de fundamentos, na CLI e na GUI; verificar com teste que o marcador é gravado nas duas vias e não é sobrescrito por mudança de campo sem carga
- [ ] 4.2 Implementar a resolução única `last_fundamentals.data` → fallback `last_date`; verificar com testes dos três casos (marcador, fallback, ausência)
- [ ] 4.3 Adicionar o nó `/fundamentos/data-referencia` a `FonteFundamentos`/`ramo_fundamentos` e injetar a data nas duas composições (`montar_core_navegacao` e `ChatPanel.montar_arvore`); verificar com teste que o nó existe e que `obter` devolve a data
- [ ] 4.4 Adicionar a operação `data_referencia` ao `NavegacaoCore` (`OPERACOES`, `CAMPOS_OBRIGATORIOS`, `_despachar`) sem campos; verificar com teste da operação e do erro de operação desconhecida
- [ ] 4.5 Adicionar o subcomando `flowscope nav data-referencia` em `cli.py`, com JSON em `stdout`; verificar com teste de CLI

## 5. Subcomandos CLI de ação (FORMA 2)

- [ ] 5.1 Registrar os subcomandos `carregar watchlist`, `atualizar fundamentos|documentos|noticias` e `resumir documentos|noticias` no parser, com dispatch em `main.py`; verificar com testes de parsing/dispatch
- [ ] 5.2 Implementar `carregar watchlist <arquivo>` (normalização, validação, persistência em `last_tickers`, JSON de saída); verificar com testes de arquivo válido e inexistente/vazio
- [ ] 5.3 Implementar `atualizar fundamentos --data D` (análise de mercado E1 + análise fundamentalista + histórico + marcador) para a watchlist; verificar com teste sobre providers fake
- [ ] 5.4 Implementar `atualizar documentos <ticker>` com validação `ticker ∈ last_tickers`; verificar com testes de ticker na watchlist e fora dela
- [ ] 5.5 Implementar `atualizar noticias`; verificar com teste sobre aquisição fake
- [ ] 5.6 Implementar `resumir documentos <ticker>` e `resumir noticias` reusando o núcleo do lote, com erro estruturado quando a LLM não está configurada; verificar com testes de pendentes e de LLM ausente

## 6. Tool MCP `nav_data_referencia`

- [ ] 6.1 Adicionar a tool ao catálogo de `presentation/navegacao.py` (sem argumentos, anotações somente-leitura, ordem alfabética) e ao dispatch; verificar com teste de `tools/list` (oito tools) e `tools/call`
- [ ] 6.2 Garantir que a tool lê só o cache local e devolve ausência de data sem `isError`; verificar com teste

## 7. Documentação

- [ ] 7.1 Atualizar `docs/misc/mcp.md` com a tool `nav_data_referencia` e reforçar que as ações de atualização são exclusivas da CLI, sem tools de ação no MCP; verificar revisão do texto
- [ ] 7.2 Atualizar `README.md` com os novos subcomandos CLI e a leitura da data de referência; verificar revisão do texto

## 8. Verificação por alteração

- [ ] 8.1 Executar `make lint` e `make complexity` e corrigir apontamentos; verificar com a saída dos comandos
- [ ] 8.2 Executar os testes relacionados/impactados pela mudança (`pytest` dos módulos tocados) e corrigir regressões; verificar com a saída do pytest
- [ ] 8.3 (Manual, usuário) Rodar a suíte completa `make test` e o `make quality-gate`, por se tratar de mudança transversal (contratos compartilhados e concorrência); verificar com a saída do quality gate
