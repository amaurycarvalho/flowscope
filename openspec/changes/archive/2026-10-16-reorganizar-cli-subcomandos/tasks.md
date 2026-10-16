## 1. Nova superfície de leitura

- [x] 1.1 Criar `src/flowscope/presentation/cli_consultas.py` espelhando `cli_acoes.py`, com `adicionar_subcomandos_consulta(subcomandos)`, `executar_exportar(args)` e `executar_consultar(args)`, movendo `run_structured_earnings`→`consultar_proventos`, `run_fatos_relevantes`→`consultar_fatos`, `run_noticias`→`consultar_noticias`, `run_regulacao`→`consultar_regulacao` e a exportação VWAP. Verificar com `python -m flowscope exportar --help` e `python -m flowscope consultar --help`.
- [x] 1.2 Declarar um parser pai `add_help=False` com `--data-inicio`/`--data-fim` e um helper `--saida`, aplicando-os apenas nos subcomandos aplicáveis. Verificar com testes de `parse_args` por subcomando (datas presentes só em `proventos`/`fatos`/`noticias`; `--categoria` só em `fatos`; `--palavra` só em `noticias`).
- [x] 1.3 Expor `--tickers` somente em `exportar vwap`, mantendo o arquivo padrão `vwap_<AAAA-MM-DD>.csv` e permitindo override por `--saida`. Verificar com teste que grava o CSV e outro que confere o nome customizado.

## 2. Parser raiz e despacho

- [x] 2.1 Remover de `build_parser` (`src/flowscope/presentation/cli.py`) as flags planas `--vwap`, `--structured-earnings`, `--fatos-relevantes`, `--noticias`, `--regulacao`, `--data-inicio`, `--data-fim`, `--output`, `--categoria`, `--palavra` e `--tickers`, registrando `exportar` e `consultar`. Verificar que `python -m flowscope --help` não exibe nenhuma dessas flags.
- [x] 2.2 Atualizar `src/flowscope/presentation/main.py`: `_tratar_modos_especiais` passa a despachar `comando in ("exportar", "consultar")` para `cli_consultas`; remover `has_cli_args`, `_handle_cli_args`, `_export` e o ramo `--mcp`. Verificar que `python -m flowscope exportar vwap` e `python -m flowscope consultar regulacao` executam o despacho esperado.
- [x] 2.3 Atualizar `_CHAVES_AUDITORIA` (`recurso`, `ticker`, `saida`, `data_inicio`, `data_fim`, `categoria`, `palavra`, `tickers`) e `_comando_principal`. Verificar com `pytest tests/test_presentation/test_main.py`.

## 3. Remoções

- [x] 3.1 Remover `run_cli` e o caminho standalone de análise por `--tickers`; remover `_load_tickers`/`export_vwap_csv` apenas se não forem reutilizados por `cli_consultas.py`. Verificar que não restam referências (`grep`) e que `make lint` passa.
- [x] 3.2 Remover o alias `--mcp`. Verificar que `python -m flowscope --mcp` falha com erro de argumento e que `python -m flowscope mcp` inicia o servidor.

## 4. Testes

- [x] 4.1 Reescrever `tests/test_presentation/test_cli.py` e `tests/test_presentation/test_cli_regulacao.py` para a nova superfície (`exportar vwap`, `consultar proventos/fatos/noticias/regulacao`, `--saida`). Verificar com `pytest tests/test_presentation/test_cli.py tests/test_presentation/test_cli_regulacao.py`.
- [x] 4.2 Ajustar `tests/test_presentation/test_main.py` e `tests/test_presentation/test_remaining_extended.py` para os novos atributos de auditoria e despacho. Verificar com `pytest tests/test_presentation`.
- [x] 4.3 Rodar `make lint` e `make complexity`.

## 5. Documentação

- [x] 5.1 Atualizar `README.md`: blocos de uso (código fonte e `dist/`), trocar `--mcp` por `mcp`, adicionar exemplos de `exportar vwap` e `consultar ...` e incluir uma tabela de migração antigo→novo.
- [x] 5.2 Atualizar `docs/misc/mcp.md`: remover a menção ao "alias legado", ajustar a configuração de cliente para `"args": ["mcp"]` e `python3 -m flowscope mcp`.
- [x] 5.3 Adicionar entrada de mudança no `CHANGELOG.md` via skill `changelog`.

## 6. Verificação final

- [x] 6.1 Rodar `make test`.
