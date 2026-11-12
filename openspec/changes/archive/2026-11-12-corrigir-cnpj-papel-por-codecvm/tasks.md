# Tasks

## 1. Resolvedor de codeCVM na B3

- [x] 1.1 Adicionar `B3FundRepository.resolver_code_cvm(ticker)` delegando ao cliente B3 e retornando `None` de forma tolerante quando o cliente não expõe o método; verificar com teste em `tests/test_infrastructure/test_b3_acquisition.py`
- [x] 1.2 Injetar `resolver_code_cvm=b3_fund_repository.resolver_code_cvm` no `CvmAcionistasSource` de `montar_nucleo` em `presentation/composicao.py`; verificar que o construtor continua compatível sem o resolvedor
- [x] 1.3 Servir o último `codeCVM` persistido quando a B3 falhar após as retentativas, sem nova gravação; verificar com teste de cache expirado + API HTTP 500 em `tests/test_infrastructure/test_regulacao/test_code_cvm_resolution.py`
- [x] 1.4 Garantir que falha de resolução sem cache persistido continua retornando `None` sem gravar cache negativo; verificar com teste em `tests/test_infrastructure/test_regulacao/test_code_cvm_resolution.py`

## 2. Cadastro de companhias abertas da CVM

- [x] 2.1 Adicionar `parse_cadastro_cia` em `infrastructure/cvm/acionistas.py` mapeando `CD_CVM` normalizado (sem zeros à esquerda) para `CNPJ_CIA` normalizado; verificar com fixture e casos de código com zeros
- [x] 2.2 Criar o downloader do cadastro (`cad_cia_aberta.csv`, CSV direto, `zipado=False`, versão do parser) e integrar ao cache normalizado por hash; verificar com testes de reaproveitamento, invalidação por versão e falha de rede
- [x] 2.3 Subir a versão do parser do cadastro para `cvm-acionistas-v3` e tolerar mapa normalizado legado em formato string; verificar que o CNPJ do Papel não desaparece com cache antigo

## 3. Fallback de CNPJ em duas etapas

- [x] 3.1 Alterar `CvmAcionistasSource._resolver_cnpj` para consultar o FCA primeiro e, em ausência, resolver o `codeCVM` e buscar no mapa do cadastro; verificar com testes para `BPAC11`, `CMIN3`, `MBRF3` e `CSNA3` com FCA sintético não literal
- [x] 3.2 Verificar a tolerância do fallback quando não há `codeCVM`, o cadastro falha ou o CNPJ é inválido: retorno `None` sem exceção e sem interromper os demais tickers
- [x] 3.3 Verificar que o caminho FCA literal continua funcionando (`PETR4`/`PETR3`) e que `obter_acionistas`/`obter_free_float` continuam usando o CNPJ resolvido para consultar o FRE

## 4. Regressão da watchlist

- [x] 4.1 Adicionar teste de regressão com os quatro tickers da watchlist (`BPAC11`, `CMIN3`, `MBRF3`, `CSNA3`) verificando o CNPJ esperado e a origem CVM
- [x] 4.2 Adicionar teste que garanta que um Papel sem FCA literal e sem codeCVM permanece sem CNPJ, sem erro

## 5. Razão social do Papel em Dados fiscais

- [x] 5.1 Estender `parse_cadastro_cia` para guardar `DENOM_SOCIAL` como `razao_social` junto do CNPJ e verificar com fixture para os quatro tickers da watchlist
- [x] 5.2 Adicionar `CvmAcionistasSource.obter_identidade_papel` retornando `(CNPJ, razão social)` e verificar com testes dos quatro tickers; garantir que FCA literal sem codeCVM mantém o CNPJ com razão social ausente
- [x] 5.3 Estender `CvmPapelCnpjProvider` para emitir `CAMPO_RAZAO_SOCIAL` via `resolver_identidade` e injetá-lo em `montar_nucleo`; verificar com testes do provider
- [x] 5.4 Adicionar `CAMPO_RAZAO_SOCIAL` aos ports, `AnaliseFundamental`, à análise fundamentalista e ao codec; verificar round-trip em `test_fundamental_history_store.py`
- [x] 5.5 Exibir `Razão social <nome>` imediatamente após `CNPJ` para Papel em `Dados fiscais`, omitindo quando ausente e mantendo FII/BDR como estão; verificar com testes de linha e atualizar o texto de ajuda da sub-aba
- [x] 5.6 Executar os testes impactados de CVM/linhas/provider/codec e verificar que passam

## 6. Quality gate da change

- [x] 6.1 Executar `make lint` e verificar que conclui sem erros
- [x] 6.2 Executar `make complexity` e verificar que conclui sem erros
- [x] 6.3 Executar os testes impactados (`tests/test_infrastructure/test_cvm_acionistas.py`, `tests/test_infrastructure/test_cvm_fund_data_provider.py`, `tests/test_infrastructure/test_b3_acquisition.py`, `tests/test_application/test_fundamental_linhas.py`, `tests/test_infrastructure/test_fundamental_history_store.py` e `tests/test_presentation/test_composicao.py`) e verificar que passam

## Workflow follow-up

- Recarregar os fundamentos da watchlist para regravar as observações do dia com o CNPJ corrigido e conferir `BPAC11`, `CMIN3`, `MBRF3` e `CSNA3` em `Dados fiscais`.
- Arquivar a change após a revisão e aprovação do projeto.
- Verificar o resultado arquivado em `openspec/specs/`.
