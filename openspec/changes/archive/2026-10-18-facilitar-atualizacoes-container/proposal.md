## Why

O servidor MCP pode ser executado em um container Docker cuja inicialização opcional atualiza fundamentos, documentos, notícias e resumos. Hoje a CLI usa a data de referência anterior quando `--data` é omitido e `resumir documentos` exige um único ticker, o que obriga o entrypoint do container a montar datas e laços sobre a watchlist. Simplificar esses comandos torna a inicialização do container mais previsível e curta.

## What Changes

- `flowscope atualizar fundamentos`, `flowscope atualizar documentos` e `flowscope atualizar noticias` passam a usar a **data de hoje** quando `--data` não for informado, em vez da data de referência resolvida. `--data` continua tendo precedência.
- `flowscope resumir documentos` passa a aceitar o ticker como argumento **opcional**: sem ticker, processa os pendentes de todos os tickers de `last_tickers` em uma única execução, com checagem única de LLM e sem abortar o lote quando um ticker falha.
- O resultado de `resumir documentos` sem ticker passa a ser `{"resultados": {<ticker>: <desfecho>}, "falha": <bool>}`. O desfecho de sucesso reusa as contagens agregadas atuais (`pendentes`, `sem_texto`, `nao_conclusivos`, `apontadores`); a falha de um ticker vira `{"erro": {"motivo": "falha_resumo", "detalhe": "..."}}`. `falha` é sempre presente e o processo encerra com código 1 se algum ticker falhar. Com ticker explícito, o formato atual é preservado.
- O entrypoint de container passa a usar `flowscope resumir documentos` sem ticker e não precisa mais percorrer a watchlist em shell. `FLOWSCOPE_REFERENCE_DATE` passa a ser um override opcional: quando ausente, as atualizações usam a data de hoje resolvida no fuso do container.
- Documentação de `docs/misc/mcp.md` e `README.md` passa a descrever o uso do MCP em container, as atualizações opcionais na inicialização, o novo default de data e o resumo de toda a watchlist.

## Capabilities

### New Capabilities

- *(nenhuma)*

### Modified Capabilities

- `cli-acoes-atualizacao`: data padrão das ações de atualização e processamento de resumos de documentos para toda a watchlist.

## Impact

- **Modificado**: `src/flowscope/presentation/cli_acoes.py` — resolução da data padrão, ticker opcional em `resumir documentos`, despacho e ajuda.
- **Modificado**: `src/flowscope/presentation/cli_resumos.py` — processamento em lote por `last_tickers`, captura de erros por ticker, saída por ticker e código de saída.
- **Modificado**: testes de `tests/test_presentation/test_cli_acoes.py` — parser, despacho, data padrão, lote completo, falha parcial, ausência de watchlist e de LLM.
- **Documentação**: `docs/misc/mcp.md` (seção 8: tabela de etapas, entrypoint, exemplos e variáveis) e `README.md` (ações de atualização e resumo).
- Nenhuma mudança de dependências, rede ou formato de cache; `nav`/MCP e a preparação nativa de `flowscope mcp` permanecem inalterados.
