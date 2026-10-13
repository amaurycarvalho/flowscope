## 1. Caminhos e configuração

- [x] 1.1 Adicionar `log_dir()` a `src/flowscope/log_paths.py` (retorna `~/.flowscope/logs`), mantendo `log_file_path()` para o processo filho do `pypdf`; verificar com teste que ambos resolvem sob o home
- [x] 1.2 Criar leitor de retenção em `src/flowscope/infrastructure/logging/` lendo `log_retention_days` de `~/.flowscope/config.json`, com padrão `7` e aceitando apenas inteiro `>= 1`; verificar com testes para valor válido, ausente, não-inteiro, menor que 1 e config ilegível

## 2. Rotação diária e housekeeping

- [x] 2.1 Implementar a limpeza por idade dos arquivos arquivados `flowscope-YYYY-MM-DD.log` (apaga data `< hoje - N`, ignora arquivos fora do padrão e o ativo, tolera `OSError`); verificar com testes de remoção, limite exato (`hoje - N` preservado), retenção customizada e ativo preservado
- [x] 2.2 Implementar o pré-passo que rotaciona o `flowscope.log` obsoleto (`mtime` anterior a hoje) para `flowscope-YYYY-MM-DD.log`, concatenando ao destino quando já existir; verificar com testes de dia anterior, mesmo dia e destino existente
- [x] 2.3 Substituir o `RotatingFileHandler` por `TimedRotatingFileHandler(when="midnight", backupCount=0, encoding="utf-8")` em `_configure_logging` e encadear `mkdir` → rolagem obsoleta → limpeza → criação do handler; verificar com teste que o handler diário é instalado e que a rotina de limpeza é chamada na inicialização
- [x] 2.4 Configurar o nome do arquivo arquivado no formato `flowscope-YYYY-MM-DD.log`, convertendo o nome padrão do `TimedRotatingFileHandler` via `namer`; verificar com testes de conversão e de nomes fora do padrão

## 3. Botão "Abrir log" abre a pasta

- [x] 3.1 Alterar `_abrir_log_flowscope` (`app_about_actions.py`) para verificar e abrir `log_dir()`; atualizar rótulo/tooltip em `widgets/about_panel.py`; verificar com testes de pasta existente e inexistente
- [x] 3.2 Atualizar a mensagem de erro técnico do `presenter.py` para apontar para `~/.flowscope/logs`; verificar com teste do texto exibido

## 4. Warnings de extração parcial/sem texto

- [x] 4.1 Registrar `WARNING` em `DocumentFlowMixin.preparar_texto` (somente em *cache miss*) para `PARCIAL` (com ticker, nome e páginas com falha) e `SEM_TEXTO` (com ticker e nome); verificar com `caplog` para os dois casos
- [x] 4.2 Garantir que reuso de cache e estados `FALHA`/`PROTEGIDO` não geram estes avisos; verificar com `caplog` que nenhum registro é emitido nesses caminhos

## 5. Regressão e verificação

- [x] 5.1 Ajustar os testes existentes que mockam `RotatingFileHandler`, `log_file_path` e o texto da mensagem técnica (`test_main.py`, `test_remaining_extended.py`, `test_version_check.py`, `test_about_tab.py`) e confirmar que seguem verdes
- [x] 5.2 Rodar `make test` e `make lint` sem falhas e executar `openspec validate logs-diarios-e-housekeeping` com sucesso (sem `--strict`, conforme a convenção do projeto)
