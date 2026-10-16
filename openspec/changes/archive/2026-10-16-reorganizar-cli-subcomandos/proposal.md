## Why

A CLI expõe hoje duas superfícies misturadas: um conjunto de flags planas no
nível raiz (`--vwap`, `--structured-earnings`, `--fatos-relevantes`,
`--noticias`, `--regulacao` e seus parâmetros contextuais) e subcomandos já
migrados (`carregar`, `atualizar`, `resumir`, `nav`, `mcp`). As flags planas
misturam parâmetros de comandos diferentes (`--output` só faz sentido para
proventos, `--categoria` para fatos relevantes, `--palavra` para notícias),
resolvem conflitos por precedência silenciosa em vez de rejeição
(`structured-earnings > fatos > noticias > regulacao > vwap`) e tornam o
`--help` enganoso. Isso torna a CLI difícil de descobrir e fácil de usar errado.

## What Changes

- **BREAKING** Reorganizar as flags de leitura em dois subcomandos por verbo:
  - `flowscope exportar vwap [--tickers ARQUIVO] [--saida ARQUIVO]` — materializa
    o VWAP calculado localmente em CSV.
  - `flowscope consultar {proventos,fatos,noticias,regulacao}` — consulta dados
    remotos da B3 e imprime JSON.
- **BREAKING** Remover as flags planas `--vwap`, `--structured-earnings`,
  `--fatos-relevantes`, `--noticias`, `--regulacao`, `--data-inicio`,
  `--data-fim`, `--output`, `--categoria`, `--palavra` do nível raiz, sem
  aliases de compatibilidade.
- **BREAKING** Aposentar o caminho standalone `flowscope --tickers ARQUIVO`
  (modo "Análise de Indicadores" via `run_cli`), não documentado e que duplica a
  análise já feita pela GUI. `--tickers` passa a existir apenas como filtro do
  `exportar vwap`.
- **BREAKING** Remover o alias legado `flowscope --mcp`; o servidor MCP passa a
  ser iniciado apenas por `flowscope mcp`.
- Renomear `--output` para `--saida` (padrão de nomenclatura em português) e
  torná-lo disponível em todos os subcomandos de leitura; `exportar vwap`
  mantém o arquivo com data no nome por padrão e `--saida` sobrescreve o nome.
- Escopar os parâmetros ao subcomando correto: `--categoria` só em
  `consultar fatos`, `--palavra` só em `consultar noticias`, datas apenas onde
  aplicáveis.
- Atualizar `README.md`, `docs/misc/mcp.md` e `openspec/specs` afetados.

## Capabilities

### New Capabilities

Nenhuma. A mudança reorganiza a superfície da CLI já existente; não introduz
capacidade nova.

### Modified Capabilities

- `cli-interface`: substitui as requirements de exportação VWAP, extração de
  earnings e argumentos regulatórios pela superfície `exportar`/`consultar`,
  remove `--output` em favor de `--saida`, aposenta o caminho `--tickers`
  standalone e remove as flags planas.
- `mcp-server`: remove a requirement de manter o alias legado `flowscope --mcp`
  e o cenário correspondente, mantendo apenas `flowscope mcp`.
- `structured-earnings-extraction`: a requirement "CLI para extração de
  proventos" passa a apontar para `flowscope consultar proventos ... --saida`.

## Impact

- Código: `src/flowscope/presentation/cli.py` (parser, `run_cli`,
  `_load_tickers`, `export_vwap_csv`, `run_structured_earnings`,
  `run_fatos_relevantes`, `run_noticias`, `run_regulacao`),
  `src/flowscope/presentation/main.py` (`_executar`, `_handle_cli_args`,
  `_export`, `_comando_principal`, `_CHAVES_AUDITORIA`), novo módulo
  `src/flowscope/presentation/cli_consultas.py`.
- Testes: `tests/test_presentation/test_cli.py`,
  `tests/test_presentation/test_cli_regulacao.py`,
  `tests/test_presentation/test_main.py`,
  `tests/test_presentation/test_remaining_extended.py`.
- Documentação: `README.md`, `docs/misc/mcp.md`.
- **BREAKING** para scripts e usuários que usam as flags planas ou o alias
  `--mcp`; não há camada de compatibilidade.
