## Why

O log da aplicação vive em um único `flowscope.log` com rotação por tamanho
(1 MB × 3 backups). Isso mistura dias no mesmo arquivo, dificulta correlacionar
eventos por data e não dá ao usuário uma política previsível de descarte — o
histórico fica limitado e opaco. Além disso, o botão "Abrir log" aponta para um
arquivo específico que pode nem ser relevante para a ocorrência investigada, e
documentos cuja extração sai parcial ou sem texto hoje são visíveis apenas na
tela, sem rastro auditável no log.

## What Changes

- **Log diário**: o arquivo ativo permanece `~/.flowscope/logs/flowscope.log`;
  à meia-noite ele é rotacionado para `flowscope-YYYY-MM-DD.log` e um novo
  arquivo ativo é aberto, de modo que cada dia corresponda a um arquivo datado.
- **Rolagem de arquivo obsoleto**: na inicialização, se o `flowscope.log` ativo
  for de um dia anterior (app ficou fechado na virada), ele é renomeado para
  `flowscope-YYYY-MM-DD.log` antes de abrir o handler diário, evitando misturar
  dias.
- **Housekeeping com retenção configurável**: na inicialização da GUI, backups
  datados com mais de `N` dias são apagados (`N` = dias anteriores a hoje,
  padrão `7`, ou seja, mantém hoje + 7 anteriores). `N` é lido de
  `~/.flowscope/config.json` (`log_retention_days`), ajustável sem recompilar.
- **Botão de log abre a pasta**: o botão "Abrir log da aplicação" passa a abrir
  o diretório `~/.flowscope/logs` no aplicativo padrão, em vez de um arquivo
  específico. A mensagem de erro técnico do apresentador aponta para a pasta.
- **Warnings de extração**: documentos das sub-abas "Documentos" e "Notícias"
  processados parcialmente (extração de texto) ou sem texto passam a registrar
  uma linha curta de `WARNING`, identificando o documento por ticker e nome e,
  no caso parcial, a quantidade de páginas com falha.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `logging`: adiciona rotação diária de arquivos, housekeeping com retenção
  configurável na inicialização, rolagem de arquivo obsoleto e os warnings de
  documento parcial/sem texto.
- `gui-about`: o acesso ao log passa a abrir o diretório de logs, não o arquivo.

## Impact

- `src/flowscope/presentation/main.py` (`_configure_logging`): rotação diária,
  pré-passo de rolagem e housekeeping.
- `src/flowscope/log_paths.py`: caminho do diretório de logs (`log_dir`),
  mantendo `log_file_path()` para o processo filho do `pypdf`.
- `src/flowscope/infrastructure/logging/`: leitor da retenção no `config.json` e
  a rotina de limpeza por idade.
- `src/flowscope/presentation/gui/app_about_actions.py` e
  `widgets/about_panel.py`: abrir a pasta e rótulo/tooltip.
- `src/flowscope/presentation/gui/presenter.py`: mensagem de erro técnico.
- `src/flowscope/presentation/gui/charts/document_flow_mixin.py`: warnings de
  extração parcial/sem texto (seam compartilhado pelas duas sub-abas).
- Testes de `_configure_logging`, do botão "Sobre" e da extração.
- O processo filho de extração (`application/extracao_orcada.py`) permanece
  inalterado, pois o arquivo ativo mantém o nome `flowscope.log`.
