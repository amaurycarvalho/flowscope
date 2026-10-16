## Context

A CLI atual mantém dois estilos em paralelo. As ações de escrita já são
subcomandos (`carregar`, `atualizar`, `resumir`), com registro isolado em
`src/flowscope/presentation/cli_acoes.py` e despacho por `args.comando` em
`src/flowscope/presentation/main.py`. As operações de leitura, porém, continuam
como flags planas no `build_parser` de
`src/flowscope/presentation/cli.py`, com parâmetros contextuais no nível raiz
(`--output`, `--categoria`, `--palavra`, `--data-inicio`, `--data-fim`) e
resolução de conflito por ordem em `main.py` (`_handle_cli_args`:
`structured-earnings > fatos > noticias > regulacao > vwap`). Ver `proposal.md`
para a motivação.

Ver também as specs do delta: `cli-interface` (nova superfície
`exportar`/`consultar`), `mcp-server` (fim do alias `--mcp`) e
`structured-earnings-extraction` (proventos sob `consultar`).

## Goals / Non-Goals

**Goals:**

- Duas superfícies de leitura com escopo de parâmetros correto e conflito
  impossível por construção (`exportar`, `consultar`).
- Reusar o padrão já existente para ações (`cli_acoes.py` + despacho por
  `args.comando`), mantendo a CLI simétrica entre leitura e escrita.
- Nomenclatura em português (`--saida`) consistente com as ações existentes.

**Non-Goals:**

- Não alterar os use cases de aplicação (`AnalyzeTickersUseCase`,
  `ExportVWAPUseCase`, `ExtrairProventosUseCase`,
  `ExtrairDadosRegulatoriosUseCase`).
- Não unificar o carregamento de arquivo de tickers (`_load_tickers` em
  `cli.py` versus `carregar_watchlist` em `cli_acoes.py`); fica como refatoração
  futura.
- Não mexer nos `nav` nem nos verbos de escrita.
- Não traduzir as flags em inglês de `nav` (`--offset`, `--limite`, `--cursor`,
  `--max`, `--regex`, `--em`).

## Decisions

### 1. Dois verbos de leitura por procedência do dado

`exportar` agrupa operações que materializam dados calculados localmente
(apenas `vwap`); `consultar` agrupa leituras de dados remotos da B3
(`proventos`, `fatos`, `noticias`, `regulacao`).

- **Por quê**: dá um critério estável para classificar futuros comandos
  ("o dado é calculado aqui ou buscado lá fora?") e evita a ambiguidade de
  `exportar` significar "qualquer saída".
- **Alternativas**: uma única umbrella `exportar` para todas as leituras
  (rejeitada: não separa consulta de materialização); separar por fonte
  (`mercado`, `regulatorio`) (rejeitada: mistura verbos de ação e domínio).

### 2. Remover as flags planas sem camada de compatibilidade

- **Por quê**: as flags não são documentadas no `README.md`; o projeto é
  pré-1.0 e já aceita quebras em migrações anteriores. Uma camada de alias
  duplicaria o parser e reintroduziria a precedência silenciosa.
- **Alternativas**: manter aliases depreciados por uma release (rejeitada:
  custo de manutenção e testes duplicados sem ganho relevante).

### 3. Aposentar o caminho standalone de análise por `--tickers`

`flowscope --tickers ARQUIVO` hoje dispara `run_cli` e imprime VWAP/CVD
(`main.py:160`). É não documentado e duplica a análise já feita pela GUI via o
mesmo `AnalyzeTickersUseCase` (`gui/controller.py:26`). `--tickers` passa a
existir apenas como filtro de `exportar vwap`.

- **Alternativas**: criar `flowscope analisar tickers ARQUIVO` (rejeitada:
  introduz superfície nova sem demanda) ou manter em `consultar` (rejeitada:
  não é consulta a dado remoto).

### 4. `--saida` uniforme com exceção de default em `exportar vwap`

`--saida <ARQUIVO>` substitui `--output`. Em `consultar *` e `exportar vwap`,
sem `--saida` a saída vai para `stdout`; exceção: `exportar vwap` mantém o
arquivo padrão `vwap_<AAAA-MM-DD>.csv` e `--saida` sobrescreve o nome.

- **Por quê**: preserva o comportamento atual de `--vwap` (sempre grava) e
  torna `--saida` um mecanismo consistente nas demais operações.

### 5. Módulo `cli_consultas.py` e parser pai para datas

Espelhar `cli_acoes.py`: novo
`src/flowscope/presentation/cli_consultas.py` com
`adicionar_subcomandos_consulta(subcomandos)`, `executar_exportar(args)` e
`executar_consultar(args)`. As datas `--data-inicio`/`--data-fim` são
declaradas uma vez em um parser `add_help=False` reutilizado via
`parents=[...]` nos subcomandos que as usam (mesmo espírito de
`_opcoes_saida`).

- **Alternativas**: manter tudo em `cli.py` (rejeitada: amplia um arquivo já
  grande e foge do padrão de `cli_acoes.py`).

### 6. Despacho e auditoria em `main.py`

`_tratar_modos_especiais` passa a reconhecer `comando in ("exportar",
"consultar")` e delega a `cli_consultas`. São removidos o ramo `--mcp`,
`has_cli_args`, `_handle_cli_args` e `_export`. `_CHAVES_AUDITORIA` e
`_comando_principal` são atualizados para os novos atributos (`recurso`,
`ticker`, `saida`, `data_inicio`, `data_fim`, `categoria`, `palavra`,
`tickers`).

## Risks / Trade-offs

- [Quebra de scripts/usuários das flags planas] → seção de migração no
  `README.md` com tabela antigo→novo e entrada no `CHANGELOG.md`.
- [Remoção de `run_cli` quebrar imports] → `AnalyzeTickersUseCase` e
  `ExportVWAPUseCase` permanecem em `application/use_cases.py` e continuam
  usados por GUI/composição e por `exportar vwap`; remover apenas `run_cli`,
  `_load_tickers` (se não reutilizada) e `export_vwap_csv` do `cli.py`.
- [Parser pai com `add_help=False` sombrear opções] → declarar cada opção em um
  único lugar e cobrir com testes de parsing por subcomando.
- [Auditoria silenciar os novos campos] → ajustar `_CHAVES_AUDITORIA` e
  `test_main.py` na mesma mudança.

## Migration Plan

1. Introduzir `exportar`/`consultar` e `cli_consultas.py`.
2. Remover as flags planas e o alias `--mcp`; ajustar despacho e auditoria.
3. Atualizar testes de apresentação para a nova superfície.
4. Atualizar `README.md` (tabela de migração), `docs/misc/mcp.md` e
   `CHANGELOG.md`.
5. Rollback: reverter o commit; não há migração de dados nem mudança de estado
   persistido, apenas a superfície de argumentos.

## Open Questions

- Se `exportar vwap` deve imprimir o caminho do arquivo gravado no `stdout`
  (comportamento atual) ou permanecer silencioso; decisão de baixo impacto que
  não altera specs nem tarefas.
