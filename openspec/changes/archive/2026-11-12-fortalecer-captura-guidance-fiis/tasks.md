# Tasks

## 1. Proveniência e compatibilidade do ledger

- [x] 1.1 Adicionar `avaliado_em`, `prompt_version` e `modelo` opcionais a `AvaliacaoGuidance` em `domain/fii/guidance.py` e verificar que a construção existente continua válida sem os novos campos
- [x] 1.2 Serializar e desserializar os novos campos em `infrastructure/guidance_store.py`, mantendo o schema v2 e a leitura tolerante a entradas antigas; verificar com testes de ida e volta, entrada sem os campos e JSON corrompido em `tests/test_infrastructure/test_guidance_store.py`

## 2. Derivação do guidance corrente

- [x] 2.1 Alterar `_corrente` em `infrastructure/guidance_store.py` para desempatar por método (`ia` antes de `deterministico`) e, no mesmo método, por `avaliado_em` mais recente; verificar com testes que reproduzem os casos `RZAK11` (`ia` 1,00–1,10 vs determinístico 1,05) e `GGRC11` (`ia` com período vs determinístico sem período)
- [x] 2.2 Manter os cenários existentes de data mais recente, ausência recente e ledger vazio; executar `pytest tests/test_infrastructure/test_guidance_store.py tests/test_application/test_fundamental_guidance.py`

## 3. Interpretação tolerante da IA e fallback

- [x] 3.1 Refatorar `_interpretar` em `application/avaliar_guidance.py` para distinguir guidance, ausência e resposta inválida; verificar com testes de `GUIDANCE: NAO`, `SIM` com valores e `SIM` sem valores
- [x] 3.2 Tornar o parsing de valores tolerante a `R$`, separador de milhar, faixa na mesma linha e sufixo “por cota”; verificar com testes unitários de `R$ 0,85`, `0,85 a 0,90` e `1.234,56`
- [x] 3.3 Tratar `GUIDANCE: SIM` sem valor interpretável como falha da IA e acionar o extrator determinístico, sem gravar ausência `ia`; verificar com teste de fallback em `tests/test_application/test_avaliar_guidance.py`
- [x] 3.4 Normalizar períodos vagos (`não especificado`, `sem período`, `N/A`) para vazio e preservar períodos reconhecidos; verificar com testes de normalização de período

## 4. Reavaliação por versão de prompt/modelo

- [x] 4.1 Definir `PROMPT_VERSION` junto de `SYSTEM_PROMPT` e obter o modelo do adaptador quando disponível; verificar que a avaliação grava a versão e o modelo (ou vazio) no ledger
- [x] 4.2 Alterar o controle por método em `AvaliarGuidanceUseCase.avaliar_rg` para reavaliar entradas `ia` com versão de prompt/modelo diferente ou ausente, preservando a entrada anterior em caso de falha; verificar com testes de versão atual, versão antiga, entrada sem versão e falha na reavaliação
- [x] 4.3 Atualizar os testes de `GuidanceService`/pendências para considerar entradas `ia` desatualizadas como acionáveis e não deixar o botão “Resumir pendentes” permanente; verificar com `pytest tests/test_application/test_document_guidance.py tests/test_presentation/test_document_guidance_flow.py`

## 5. Diagnóstico de conflito IA x determinístico

- [x] 5.1 Quando a IA concluir ausência em todas as fontes, executar o extrator determinístico apenas para diagnóstico e registrar warning com ticker, data, valores e período quando houver divergência, sem alterar o ledger; verificar com teste que a entrada `ia` permanece ausente e o log é emitido
- [x] 5.2 Verificar que, sem divergência, nenhum warning de conflito é emitido; executar `pytest tests/test_application/test_avaliar_guidance.py`

## 6. Integração e quality gate

- [x] 6.1 Adicionar teste de integração com ledger sintético da watchlist contendo entradas `ia` e `deterministico` na mesma data e verificar que a análise fundamentalista expõe o guidance da IA e o período esperado
- [x] 6.2 Executar `make lint` e verificar que conclui sem erros
- [x] 6.3 Executar `make complexity` e verificar que conclui sem erros
- [x] 6.4 Executar os testes impactados (`tests/test_infrastructure/test_guidance_store.py`, `tests/test_application/test_avaliar_guidance.py`, `tests/test_application/test_document_guidance.py`, `tests/test_application/test_fundamental_guidance.py`) e verificar que passam

## Workflow follow-up

- Reavaliar a watchlist pelo fluxo normal de leitura/“Resumir pendentes” para atualizar as entradas antigas sem versão e conferir `RZAK11`/`GGRC11` na tabela.
- Arquivar a change após a revisão e aprovação do projeto.
- Verificar o resultado arquivado em `openspec/specs/`.
